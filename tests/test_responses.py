import json

import pytest
from scrapy import Request
from scrapy.http.response.text import TextResponse
from scrapy.utils.reqser import request_to_dict
from testfixtures import LogCapture

from zyte_proxy_fetch.middleware import SmartProxyManagerFetchException

from tests.data.responses import test_responses
from tests.utils import foo_spider, get_test_middleware, mocked_time


def test_process_response_disabled():
    middleware = get_test_middleware(settings={"ZYTE_PROXY_FETCH_ENABLED": False})
    for case in test_responses:
        response = case["original"]
        assert middleware.process_response(response.request, response, foo_spider) is response


def test_process_response():
    middleware = get_test_middleware()

    for case in test_responses:
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_response(original.request, original, foo_spider)

        assert type(processed) is type(expected)
        assert processed.url == expected.url
        assert processed.status == expected.status
        assert processed.headers == expected.headers
        assert processed.body == expected.body

        zyte_proxy_meta = processed.meta.get("zyte_proxy_fetch") or {}
        if zyte_proxy_meta.get("upstream_response"):
            assert zyte_proxy_meta["upstream_response"]["body"] == json.loads(original.text)
            assert zyte_proxy_meta["upstream_response"]["headers"] == original.headers
            assert zyte_proxy_meta["upstream_response"]["status"] == original.status


def test_process_response_skip():
    response = TextResponse(
        url="https://example.org",
        status=200,
        headers={
            "Content-Encoding": "gzip",
            "Transfer-Encoding": "chunked",
            "Date": "Fri, 24 Apr 2020 18:06:42 GMT",
        },
        request=Request(
            url="https://example.org",
            meta={"zyte_proxy_fetch": {"skip": True}},
        ),
        body=b"""<html></html>""",
    )

    middleware = get_test_middleware()
    processed = middleware.process_response(response.request, response, foo_spider)

    assert response is processed


def test_process_response_error():
    response_list = [
        TextResponse(
            url="https://zyte.com/fake/api/endpoint",
            request=Request(
                url="https://zyte.com/fake/api/endpoint",
                meta={
                    "zyte_proxy_fetch": {
                        "timing": {"start_ts": mocked_time()},
                        "original_request": request_to_dict(
                            Request("https://example.org"),
                            spider=foo_spider,
                        ),
                    }
                },
            ),
            headers={
                "X-Crawlera-Error": "bad_proxy_auth",
                "Proxy-Authenticate": 'Basic realm="Crawlera"',
                "Content-Length": "0",
                "Date": "Mon, 04 May 2020 13:06:15 GMT",
                "Proxy-Connection": "close",
                "Connection": "close",
            },
        ),
        TextResponse(
            url="https://zyte.com/fake/api/endpoint",
            request=Request(
                url="https://zyte.com/fake/api/endpoint",
                meta={
                    "zyte_proxy_fetch": {
                        "timing": {"start_ts": mocked_time()},
                        "original_request": request_to_dict(
                            Request("https://example.org"),
                            spider=foo_spider,
                        ),
                    }
                },
            ),
            body=b'{"Bad": "JSON',
        ),
        TextResponse(
            url="https://zyte.com/fake/api/endpoint",
            request=Request(
                url="https://zyte.com/fake/api/endpoint",
                meta={
                    "zyte_proxy_fetch": {
                        "timing": {"start_ts": mocked_time()},
                        "original_request": request_to_dict(
                            Request("https://example.org"),
                            spider=foo_spider,
                        ),
                    }
                },
            ),
            body=json.dumps(
                {
                    "url": "https://example.org",
                    "original_status": 503,
                    "headers": {},
                    "crawlera_status": "fail",
                    "crawlera_error": "serverbusy",
                    "body_encoding": "plain",
                    "body": "Server busy: too many outstanding requests",
                }
            ),
            encoding="utf8",
        ),
    ]

    middleware_raise = get_test_middleware(settings={"ZYTE_PROXY_FETCH_RAISE_ON_ERROR": True})
    for response in response_list:
        with pytest.raises(SmartProxyManagerFetchException):
            middleware_raise.process_response(response.request, response, foo_spider)

    assert middleware_raise.stats.get_value("zyte_proxy_fetch/response_error") == 3
    assert middleware_raise.stats.get_value("zyte_proxy_fetch/response_error/bad_proxy_auth") == 1
    assert middleware_raise.stats.get_value("zyte_proxy_fetch/response_error/JSONDecodeError") == 1
    assert middleware_raise.stats.get_value("zyte_proxy_fetch/response_error/serverbusy") == 1

    middleware_log = get_test_middleware(settings={"ZYTE_PROXY_FETCH_RAISE_ON_ERROR": False})
    with LogCapture() as logs:
        for response in response_list:
            processed = middleware_log.process_response(response.request, response, foo_spider)
            assert response is processed

    logs.check_present(
        (
            "zyte-proxy-fetch-middleware",
            "WARNING",
            "Error downloading <GET https://example.org> (status: 200, X-Crawlera-Error header: bad_proxy_auth)",  # noqa: E501
        ),
        (
            "zyte-proxy-fetch-middleware",
            "WARNING",
            "Error decoding <GET https://example.org> (status: 200, message: Unterminated string starting at, lineno: 1, colno: 9)",  # noqa: E501
        ),
        (
            "zyte-proxy-fetch-middleware",
            "WARNING",
            "Error downloading <GET https://example.org> (Original status: 503, Fetch API error message: Server busy: too many outstanding requests, Request ID: unknown)",  # noqa: E501
        ),
    )

    assert middleware_log.stats.get_value("zyte_proxy_fetch/response_error") == 3
    assert middleware_log.stats.get_value("zyte_proxy_fetch/response_error/bad_proxy_auth") == 1
    assert middleware_log.stats.get_value("zyte_proxy_fetch/response_error/JSONDecodeError") == 1
    assert middleware_log.stats.get_value("zyte_proxy_fetch/response_error/serverbusy") == 1
