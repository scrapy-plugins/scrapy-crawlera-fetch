import unittest
from copy import deepcopy
from logging import LogRecord, Formatter

from scrapy import Spider, version_info as scrapy_version
from scrapy.http.response import Response
from scrapy.utils.test import get_crawler
from twisted.python.failure import Failure

from crawlera_fetch_middleware.logformatter import CrawleraFetchLogFormatter
from crawlera_fetch_middleware.middleware import CrawleraFetchMiddleware

from tests.data import SETTINGS
from tests.data.requests import test_requests


@unittest.skipIf(scrapy_version > (2, 0, 0), "Scrapy < 2.0 only")
def test_log_formatter_scrapy_1():
    middleware = CrawleraFetchMiddleware(get_crawler(settings_dict=SETTINGS))
    logformatter = CrawleraFetchLogFormatter()
    formatter = Formatter()
    spider = Spider("foo")

    for case in deepcopy(test_requests):
        original = case["original"]
        response = Response(original.url)
        processed = middleware.process_request(original, spider)

        # crawled
        result = logformatter.crawled(processed, response, spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        expected = "Crawled (200) {request} ['Original URL: {url}'] (referer: None)".format(
            request=original, url=original.url
        )
        assert logstr == expected


@unittest.skipIf(scrapy_version < (2, 0, 0), "Scrapy >= 2.0 only")
def test_log_formatter_scrapy_2():
    middleware = CrawleraFetchMiddleware(get_crawler(settings_dict=SETTINGS))
    logformatter = CrawleraFetchLogFormatter()
    formatter = Formatter()
    spider = Spider("foo")

    for case in deepcopy(test_requests):
        original = case["original"]
        response = Response(original.url)
        processed = middleware.process_request(original, spider)

        # crawled
        result = logformatter.crawled(processed, response, spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Crawled (200) %s (referer: None)" % str(original)

        # spider_error
        result = logformatter.spider_error(Failure(Exception("exc")), processed, response, spider)
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=1, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Spider error processing %s (referer: None)" % str(original)

        # download_error
        result = logformatter.download_error(Failure(Exception("exc")), processed, spider, "foo")
        assert result["args"]["request"] == str(original)
        record = LogRecord(name="logger", pathname="n/a", lineno=2, exc_info=None, **result)
        logstr = formatter.format(record)
        assert logstr == "Error downloading %s: foo" % str(original)
