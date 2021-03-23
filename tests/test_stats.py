import json
import random
from unittest.mock import patch

from scrapy import Spider, Request
from scrapy.http.response.text import TextResponse

from tests.utils import get_test_middleware


@patch("time.time")
def test_stats(mocked_time):
    middleware = get_test_middleware()
    spider = Spider("foo")

    count = 100
    nums = list(range(count))
    random.shuffle(nums)
    status_list = [random.randint(1, 15) for _ in range(count)]
    method_list = [random.choice(["GET", "POST", "PUT", "DELETE", "HEAD"]) for _ in range(count)]

    # expected values
    latencies = [2 ** n - n for n in nums]
    total_latency = sum(latencies)
    avg_latency = total_latency / count
    max_latency = max(latencies)

    for n, status, method in zip(nums, status_list, method_list):
        request = Request("https://example.org", method=method)
        mocked_time.return_value = n  # start_ts
        processed_request = middleware.process_request(request, spider)

        response = TextResponse(
            url="https://example.org",
            request=processed_request,
            body=json.dumps(
                {"headers": {}, "original_status": status, "body": "", "url": "http://"}
            ).encode("utf-8"),
        )

        mocked_time.return_value = 2 ** n  # end_ts
        middleware.process_response(processed_request, response, spider)

    middleware.spider_closed(spider, "finished")

    assert middleware.stats.get_value("zyte_proxy_fetch/request_count") == count
    assert middleware.stats.get_value("zyte_proxy_fetch/response_count") == count
    assert middleware.stats.get_value("zyte_proxy_fetch/total_latency") == total_latency
    assert middleware.stats.get_value("zyte_proxy_fetch/avg_latency") == avg_latency
    assert middleware.stats.get_value("zyte_proxy_fetch/max_latency") == max_latency
    for status in set(status_list):
        sc = middleware.stats.get_value("zyte_proxy_fetch/response_status_count/{}".format(status))
        assert sc == status_list.count(status)
    for method in set(method_list):
        mc = middleware.stats.get_value("zyte_proxy_fetch/request_method_count/{}".format(method))
        assert mc == method_list.count(method)
