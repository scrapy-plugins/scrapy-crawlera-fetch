import json

import pytest
from scrapy import Spider, Request
from scrapy.http.response.text import TextResponse
from testfixtures import LogCapture

from crawlera_fetch.middleware import CrawleraFetchException

from tests.data.responses import test_responses
from tests.utils import get_test_middleware


def test_process_response():
    middleware = get_test_middleware()

    for case in test_responses:
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_response(original.request, original, Spider("foo"))

        assert type(processed) is type(expected)
        assert processed.url == expected.url
        assert processed.status == expected.status
        assert processed.headers == expected.headers
        assert processed.body == expected.body

        crawlera_meta = processed.meta.get("crawlera_fetch") or {}
        if crawlera_meta.get("upstream_response"):
            assert crawlera_meta["upstream_response"]["body"] == json.loads(original.text)
            assert crawlera_meta["upstream_response"]["headers"] == original.headers
            assert crawlera_meta["upstream_response"]["status"] == original.status


def test_process_response_skip():
    response = TextResponse(
        url="https://example.org",
        status=200,
        headers={
            "Content-Encoding": "gzip",
            "Transfer-Encoding": "chunked",
            "Date": "Fri, 24 Apr 2020 18:06:42 GMT",
        },
        request=Request(url="https://example.org", meta={"crawlera_fetch": {"skip": True}}),
        body=b"""<html></html>""",
    )

    middleware = get_test_middleware()
    processed = middleware.process_response(response.request, response, Spider("foo"))

    assert response is processed


def test_process_response_error():
    response_list = [
        TextResponse(
            url="https://crawlera.com/fake/api/endpoint",
            request=Request(
                url="https://crawlera.com/fake/api/endpoint",
                meta={
                    "crawlera_fetch": {
                        "original_request": {"url": "https://example.org", "method": "GET"}
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
            url="https://crawlera.com/fake/api/endpoint",
            request=Request(
                url="https://crawlera.com/fake/api/endpoint",
                meta={
                    "crawlera_fetch": {
                        "original_request": {"url": "https://example.org", "method": "GET"}
                    }
                },
            ),
            body=b'{"Bad": "JSON',
        ),
    ]

    middleware_raise = get_test_middleware(settings={"CRAWLERA_FETCH_RAISE_ON_ERROR": True})
    for response in response_list:
        with pytest.raises(CrawleraFetchException):
            middleware_raise.process_response(response.request, response, Spider("foo"))

    assert middleware_raise.stats.get_value("crawlera_fetch/response_error") == 2
    assert middleware_raise.stats.get_value("crawlera_fetch/response_error/bad_proxy_auth") == 1
    assert middleware_raise.stats.get_value("crawlera_fetch/response_error/JSONDecodeError") == 1

    middleware_log = get_test_middleware(settings={"CRAWLERA_FETCH_RAISE_ON_ERROR": False})
    with LogCapture() as logs:
        for response in response_list:
            processed = middleware_log.process_response(response.request, response, Spider("foo"))
            assert response is processed

    logs.check_present(
        (
            "crawlera-fetch-middleware",
            "ERROR",
            "Error downloading <GET https://example.org> (status: 200, X-Crawlera-Error header: bad_proxy_auth)",  # noqa: E501
        ),
        (
            "crawlera-fetch-middleware",
            "ERROR",
            "Error decoding <GET https://example.org> (status: 200, message: Unterminated string starting at, lineno: 1, colno: 9)",  # noqa: E501
        ),
    )

    assert middleware_log.stats.get_value("crawlera_fetch/response_error") == 2
    assert middleware_log.stats.get_value("crawlera_fetch/response_error/bad_proxy_auth") == 1
    assert middleware_log.stats.get_value("crawlera_fetch/response_error/JSONDecodeError") == 1
