import json

from scrapy import Spider

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
