import json

from scrapy import Request, FormRequest
from w3lib.http import basic_auth_header

from tests.data import SETTINGS


test_requests = []

test_requests.append(
    {
        "original": Request(
            url="https://httpbin.org/anything",
            method="GET",
            meta={
                "crawlera_fetch": {
                    "render": "no",
                    "region": "us",
                    "iptype": "datacenter",
                    "device": "mobile",
                }
            },
        ),
        "expected": Request(
            url=SETTINGS["CRAWLERA_FETCH_URL"],
            method="POST",
            headers={
                "Authorization": basic_auth_header(SETTINGS["CRAWLERA_FETCH_APIKEY"], ""),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            meta={
                "crawlera_fetch_original_request": {
                    "url": "https://httpbin.org/anything",
                    "method": "GET",
                    "headers": {},
                    "body": b"",
                },
                "crawlera_fetch": {
                    "render": "no",
                    "region": "us",
                    "iptype": "datacenter",
                    "device": "mobile",
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
        ),
    }
)

test_requests.append(
    {
        "original": FormRequest(
            url="https://httpbin.org/post",
            meta={"crawlera_fetch": {"device": "desktop"}},
            formdata={"foo": "bar"},
        ),
        "expected": FormRequest(
            url=SETTINGS["CRAWLERA_FETCH_URL"],
            method="POST",
            headers={
                "Authorization": basic_auth_header(SETTINGS["CRAWLERA_FETCH_APIKEY"], ""),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            meta={
                "crawlera_fetch_original_request": {
                    "url": "https://httpbin.org/post",
                    "method": "POST",
                    "headers": {b"Content-Type": [b"application/x-www-form-urlencoded"]},
                    "body": b"foo=bar",
                },
                "crawlera_fetch": {"device": "desktop"},
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
        ),
    }
)

test_requests.append(
    {
        "original": Request(
            url="https://example.org", method="HEAD", meta={"crawlera_fetch_skip": True},
        ),
        "expected": None,
    }
)
