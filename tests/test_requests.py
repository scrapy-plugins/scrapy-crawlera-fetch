import json
from copy import deepcopy

from scrapy import Spider

from tests.data.requests import test_requests
from tests.utils import get_test_middleware


def test_process_request():
    middleware = get_test_middleware()

    for case in deepcopy(test_requests):
        original = case["original"]
        expected = case["expected"]

        processed = middleware.process_request(original, Spider("foo"))

        if original.meta.get("crawlera_fetch_skip"):
            assert processed is None
        else:
            assert type(processed) is type(expected)
            assert processed.url == expected.url
            assert processed.method == expected.method
            assert processed.headers == expected.headers
            assert processed.meta == expected.meta
            processed_text = processed.body.decode(processed.encoding)
            expected_text = expected.body.decode(expected.encoding)
            assert json.loads(processed_text) == json.loads(expected_text)
