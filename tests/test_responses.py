from scrapy import Spider, Request
from scrapy.utils.test import get_crawler

from crawlera_fetch import CrawleraFetchMiddleware

from tests.data import SETTINGS
from tests.data.responses import test_responses


def test_process_request():
    middleware = CrawleraFetchMiddleware.from_crawler(get_crawler(settings_dict=SETTINGS))

    for case in test_responses:
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_response(
            Request(SETTINGS["CRAWLERA_FETCH_URL"]), original, Spider("foo")
        )

        assert type(processed) is type(expected)
        assert processed.url == expected.url
        assert processed.status == expected.status
        assert processed.headers == expected.headers
        assert processed.body == expected.body
