from scrapy import Request

from crawlera_fetch.middleware import OnError

from tests.data.responses import get_test_responses, get_test_responses_error
from tests.utils import foo_spider, get_test_middleware


def test_process_response_should_retry_function():
    def retry_function(response, request, spider):
        return True

    middleware = get_test_middleware(settings={"CRAWLERA_FETCH_SHOULD_RETRY": retry_function})
    for case in get_test_responses(include_unprocessed=False):
        response = case["original"]
        result = middleware.process_response(response.request, response, foo_spider)
        assert isinstance(result, Request)
        assert result.url == response.request.url

    base_key = "crawlera_fetch/retry/should-retry"
    assert middleware.stats.get_value(f"{base_key}/count") == 4
    assert middleware.stats.get_value(f"{base_key}/reason_count/should-retry") == 4


def test_process_response_should_retry_spider_method():
    middleware = get_test_middleware(settings={"CRAWLERA_FETCH_SHOULD_RETRY": "should_retry"})
    for case in get_test_responses(include_unprocessed=False):
        response = case["original"]
        result = middleware.process_response(response.request, response, foo_spider)
        assert isinstance(result, Request)
        assert result.url == response.request.url

    base_key = "crawlera_fetch/retry/should-retry"
    assert middleware.stats.get_value(f"{base_key}/count") == 4
    assert middleware.stats.get_value(f"{base_key}/reason_count/should-retry") == 4


def test_process_response_error():
    middleware = get_test_middleware(settings={"CRAWLERA_FETCH_ON_ERROR": OnError.Retry})
    for response in get_test_responses_error():
        result = middleware.process_response(response.request, response, foo_spider)
        assert isinstance(result, Request)
        assert result.url == response.request.url

    base_key = "crawlera_fetch/retry/error"
    assert middleware.stats.get_value(f"{base_key}/count") == 3
    assert middleware.stats.get_value(f"{base_key}/reason_count/bad_proxy_auth") == 1
    assert middleware.stats.get_value(f"{base_key}/reason_count/json.decoder.JSONDecodeError") == 1
    assert middleware.stats.get_value(f"{base_key}/reason_count/serverbusy") == 1
