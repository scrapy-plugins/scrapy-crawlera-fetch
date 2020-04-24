from scrapy import Spider, Request
from scrapy.utils.test import get_crawler

from simple_fetch_middleware import CrawleraSimpleFetchMiddleware

from tests.data.responses import test_responses


SETTINGS = {
    "CRAWLERA_ENABLED": True,
    "CRAWLERA_URL": "https://example.org",
    "CRAWLERA_APIKEY": "12345",
}


def test_process_request():
    middleware = CrawleraSimpleFetchMiddleware(get_crawler(settings_dict=SETTINGS))

    for case in test_responses:
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_response(
            request=Request(SETTINGS["CRAWLERA_URL"]), response=original, spider=Spider("foo")
        )

        assert type(processed) is type(expected)
        assert processed.url == expected.url
        assert processed.status == expected.status
        assert processed.headers == expected.headers
        assert processed.body == expected.body
