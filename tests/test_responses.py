import json

from scrapy import Spider, Request
from scrapy.http.response import Response

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

        if processed.meta.get("crawlera_fetch_response"):
            assert processed.meta["crawlera_fetch_response"]["body"] == json.loads(original.text)
            assert processed.meta["crawlera_fetch_response"]["headers"] == original.headers
            assert processed.meta["crawlera_fetch_response"]["status"] == original.status


def test_process_response_skip():
    response = Response(
        url="https://example.org",
        status=200,
        headers={
            "Content-Encoding": "gzip",
            "Transfer-Encoding": "chunked",
            "Date": "Fri, 24 Apr 2020 18:06:42 GMT",
        },
        request=Request(url="https://example.org", meta={"crawlera_fetch_skip": True}),
        body=b"""<html></html>""",
    )

    middleware = get_test_middleware()
    processed = middleware.process_response(response.request, response, Spider("foo"))

    assert response is processed


def test_process_response_error():
    response = Response(
        url="https://crawlera.com/fake/api/endpoint",
        request=Request(
            url="https://crawlera.com/fake/api/endpoint",
            meta={
                "crawlera_fetch_original_request": {"url": "https://example.org", "method": "GET"}
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
    )

    middleware = get_test_middleware()
    processed = middleware.process_response(response.request, response, Spider("foo"))

    assert response is processed
    assert middleware.stats.get_value("crawlera_fetch/response_error") == 1
    assert middleware.stats.get_value("crawlera_fetch/response_error/bad_proxy_auth") == 1
