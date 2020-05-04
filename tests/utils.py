from urllib.parse import urlparse

from scrapy import Spider
from scrapy.utils.test import get_crawler

from crawlera_fetch.middleware import CrawleraFetchMiddleware

from tests.data import SETTINGS


class MockDownloader:
    def _get_slot_key(self, request, spider):
        if "download_slot" in request.meta:
            return request.meta["download_slot"]
        return urlparse(request.url).hostname or ""


class MockEngine:
    def __init__(self):
        self.downloader = MockDownloader()


class FooSpider(Spider):
    name = "foo"


def get_test_middleware():
    crawler = get_crawler(FooSpider, settings_dict=SETTINGS)
    crawler.engine = MockEngine()
    middleware = CrawleraFetchMiddleware.from_crawler(crawler)
    return middleware
