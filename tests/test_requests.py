import json

from scrapy import Spider
from scrapy.utils.test import get_crawler

from simple_fetch_middleware import CrawleraSimpleFetchMiddleware

from tests.data.requests import test_requests


SETTINGS = {
    "CRAWLERA_ENABLED": True,
    "CRAWLERA_URL": "https://example.org",
    "CRAWLERA_APIKEY": "12345",
}


def test_process_request():
    middleware = CrawleraSimpleFetchMiddleware(get_crawler(settings_dict=SETTINGS))

    for case in test_requests:
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_request(original, Spider("foo"))

        assert type(processed) is type(expected)
        assert processed.url == expected.url
        assert processed.method == expected.method
        assert processed.headers == expected.headers
        assert processed.meta == expected.meta
        processed_text = processed.body.decode(processed.encoding)
        expected_text = expected.body.decode(expected.encoding)
        assert json.loads(processed_text) == json.loads(expected_text)
