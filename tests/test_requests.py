import json
from copy import deepcopy

from scrapy import Spider
from scrapy.utils.test import get_crawler

from crawlera_fetch import CrawleraFetchMiddleware

from tests.data import SETTINGS
from tests.data.requests import test_requests


def test_process_request():
    middleware = CrawleraFetchMiddleware.from_crawler(get_crawler(settings_dict=SETTINGS))

    for case in deepcopy(test_requests):
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
