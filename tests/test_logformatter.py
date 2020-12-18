import unittest
from copy import deepcopy
from logging import LogRecord, Formatter

from scrapy import version_info as scrapy_version
from scrapy.http.response import Response
from twisted.python.failure import Failure

from crawlera_fetch.logformatter import CrawleraFetchLogFormatter

from tests.data.requests import test_requests
from tests.utils import foo_spider, get_test_middleware


@unittest.skipIf(scrapy_version > (2, 0, 0), "Scrapy < 2.0 only")
def test_log_formatter_scrapy_1():
    middleware = get_test_middleware()
    logformatter = CrawleraFetchLogFormatter()
    formatter = Formatter()

    for case in deepcopy(test_requests):
        original = case["original"]
        response = Response(original.url)
        processed = middleware.process_request(original, foo_spider)

        crawlera_meta = original.meta.get("crawlera_fetch") or {}
        if crawlera_meta.get("skip"):
            assert processed is None
            continue

        # crawled
        result = logformatter.crawled(processed, response, foo_spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        expected = "Crawled (200) {request} ['original url: {url}'] (referer: None)".format(
            request=original, url=original.url
        )
        assert logstr == expected


@unittest.skipIf(scrapy_version < (2, 0, 0), "Scrapy >= 2.0 only")
def test_log_formatter_scrapy_2():
    middleware = get_test_middleware()
    logformatter = CrawleraFetchLogFormatter()
    formatter = Formatter()

    for case in deepcopy(test_requests):
        original = case["original"]
        response = Response(original.url)
        processed = middleware.process_request(original, foo_spider)

        crawlera_meta = original.meta.get("crawlera_fetch") or {}
        if crawlera_meta.get("skip"):
            assert processed is None
            continue

        # crawled
        result = logformatter.crawled(processed, response, foo_spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Crawled (200) %s (referer: None)" % str(original)

        # spider_error
        result = logformatter.spider_error(Failure(Exception("exc")), processed, response, foo_spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Spider error processing %s (referer: None)" % str(original)

        # download_error
        result = logformatter.download_error(Failure(Exception("exc")), processed, foo_spider, "error")
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=2, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Error downloading %s: error" % str(original)
