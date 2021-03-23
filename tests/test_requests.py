import json
import os
from contextlib import contextmanager
from unittest.mock import patch

from scrapy import Request

from zyte_proxy_fetch import DownloadSlotPolicy

from tests.data.requests import get_test_requests
from tests.utils import foo_spider, get_test_middleware, mocked_time


@contextmanager
def shub_jobkey_env_variable():
    SHUB_JOBKEY_OLD = os.environ.get("SHUB_JOBKEY")
    os.environ["SHUB_JOBKEY"] = "1/2/3"
    try:
        yield
    finally:
        del os.environ["SHUB_JOBKEY"]
        if SHUB_JOBKEY_OLD:
            os.environ["SHUB_JOBKEY"] = SHUB_JOBKEY_OLD


@patch("time.time", mocked_time)
def test_process_request():
    middleware = get_test_middleware()

    for case in get_test_requests():
        original = case["original"]
        expected = case["expected"]

        with shub_jobkey_env_variable():
            processed = middleware.process_request(original, foo_spider)

        zyte_proxy_meta = original.meta.get("zyte_proxy_fetch")
        if zyte_proxy_meta.get("skip"):
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


@patch("time.time", mocked_time)
def test_process_request_single_download_slot():
    middleware = get_test_middleware(
        settings={"ZYTE_PROXY_FETCH_DOWNLOAD_SLOT_POLICY": DownloadSlotPolicy.Single}
    )

    for case in get_test_requests():
        original = case["original"]
        expected = case["expected"]
        if expected:
            expected.meta["download_slot"] = "__zyte_proxy_fetch__"

        with shub_jobkey_env_variable():
            processed = middleware.process_request(original, foo_spider)

        zyte_proxy_meta = original.meta.get("zyte_proxy_fetch")
        if zyte_proxy_meta.get("skip"):
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


@patch("time.time", mocked_time)
def test_process_request_default_args():
    middleware = get_test_middleware(
        settings={"ZYTE_PROXY_FETCH_DEFAULT_ARGS": {"foo": "bar", "answer": "42"}}
    )

    for case in get_test_requests():
        original = case["original"]
        processed = middleware.process_request(original, foo_spider)

        zyte_proxy_meta = original.meta.get("zyte_proxy_fetch")
        if zyte_proxy_meta.get("skip"):
            assert processed is None
        else:
            processed_text = processed.body.decode(processed.encoding)
            processed_json = json.loads(processed_text)
            assert processed_json["foo"] == "bar"
            assert processed_json["answer"] == "42"


@patch("scrapy.version_info", (1, 8, 0))
def test_process_request_scrapy_1():
    from tests.utils import get_test_middleware

    middleware = get_test_middleware()
    request = Request("https://example.org")
    with shub_jobkey_env_variable():
        processed = middleware.process_request(request, foo_spider)
    assert processed.flags == ["original url: https://example.org"]
