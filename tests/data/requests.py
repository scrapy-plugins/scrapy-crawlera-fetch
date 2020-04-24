import json

from scrapy import Request, FormRequest


test_requests = []

test_requests.append(
    {
        "original": Request(
            url="https://httpbin.org/anything",
            method="GET",
            meta={
                "crawlera": {
                    "render": "no",
                    "region": "us",
                    "iptype": "datacenter",
                    "device": "mobile",
                }
            },
        ),
        "expected": Request(
            url="https://example.org",
            method="POST",
            headers={
                "Authorization": ["Basic MTIzNDU6"],
                "Content-Type": ["application/json"],
                "Accept": ["application/json"],
            },
            meta={
                "crawlera_processed": True,
                "crawlera": {
                    "render": "no",
                    "region": "us",
                    "iptype": "datacenter",
                    "device": "mobile",
                },
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
            meta={"crawlera": {"device": "desktop"}},
            formdata={"foo": "bar"},
        ),
        "expected": FormRequest(
            url="https://example.org",
            method="POST",
            headers={
                "Authorization": ["Basic MTIzNDU6"],
                "Content-Type": ["application/json"],
                "Accept": ["application/json"],
            },
            meta={"crawlera_processed": True, "crawlera": {"device": "desktop"}},
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
