import json
from copy import deepcopy
from unittest.mock import patch

from scrapy import Spider, Request

from crawlera_fetch import DownloadSlotPolicy

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


def test_process_request_single_download_slot():
    middleware = get_test_middleware(
        settings={"CRAWLERA_FETCH_DOWNLOAD_SLOT_POLICY": DownloadSlotPolicy.Single}
    )

    for case in deepcopy(test_requests):
        original = case["original"]
        expected = case["expected"]
        if expected:
            expected.meta["download_slot"] = "__crawlera_fetch__"

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


@patch("scrapy.version_info", (1, 8, 0))
def test_process_request_scrapy_1():
    from tests.utils import get_test_middleware

    middleware = get_test_middleware()
    request = Request("https://example.org")
    processed = middleware.process_request(request, Spider("foo"))
    assert processed.flags == ["original url: https://example.org"]
