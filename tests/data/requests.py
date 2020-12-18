import json

from scrapy import Request, FormRequest
from scrapy.utils.reqser import request_to_dict
from w3lib.http import basic_auth_header

from tests.data import SETTINGS
from tests.utils import foo_spider, mocked_time


test_requests = []

original1 = Request(
    url="https://httpbin.org/anything",
    method="GET",
    meta={
        "crawlera_fetch": {
            "args": {
                "render": "no",
                "region": "us",
                "iptype": "datacenter",
                "device": "mobile",
            }
        }
    },
)
expected1 = Request(
    url=SETTINGS["CRAWLERA_FETCH_URL"],
    callback=foo_spider.foo_callback,
    method="POST",
    headers={
        "Authorization": basic_auth_header(SETTINGS["CRAWLERA_FETCH_APIKEY"], ""),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Crawlera-JobId": "1/2/3",
    },
    meta={
        "crawlera_fetch": {
            "args": {
                "render": "no",
                "region": "us",
                "iptype": "datacenter",
                "device": "mobile",
            },
            "original_request": request_to_dict(original1, spider=foo_spider),
            "timing": {"start_ts": mocked_time()},
        },
        "download_slot": "httpbin.org",
    },
    body=json.dumps(
        {
            "url": "https://httpbin.org/anything",
            "method": "GET",
            "body": "",
            "render": "no",
            "region": "us",
            "iptype": "datacenter",
            "device": "mobile",
        }
    ),
)
test_requests.append(
    {
        "original": original1,
        "expected": expected1,
    }
)


original2 = FormRequest(
    url="https://httpbin.org/post",
    callback=foo_spider.foo_callback,
    meta={"crawlera_fetch": {"args": {"device": "desktop"}}},
    formdata={"foo": "bar"},
)
expected2 = FormRequest(
    url=SETTINGS["CRAWLERA_FETCH_URL"],
    method="POST",
    headers={
        "Authorization": basic_auth_header(SETTINGS["CRAWLERA_FETCH_APIKEY"], ""),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Crawlera-JobId": "1/2/3",
    },
    meta={
        "crawlera_fetch": {
            "args": {"device": "desktop"},
            "original_request": request_to_dict(original2, spider=foo_spider),
            "timing": {"start_ts": mocked_time()},
        },
        "download_slot": "httpbin.org",
    },
    body=json.dumps(
        {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "body": "foo=bar",
            "device": "desktop",
        }
    ),
)
test_requests.append(
    {
        "original": original2,
        "expected": expected2,
    }
)

test_requests.append(
    {
        "original": Request(
            url="https://example.org",
            method="HEAD",
            meta={"crawlera_fetch": {"skip": True}},
        ),
        "expected": None,
    }
)
