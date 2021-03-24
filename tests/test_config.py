from scrapy import Spider
from scrapy.utils.test import get_crawler

from crawlera_fetch import CrawleraFetchMiddleware

from tests.data import SETTINGS


def test_disable_via_setting():
    class FooSpider(Spider):
        name = "foo"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(FooSpider, settings_dict={"CRAWLERA_FETCH_ENABLED": False})
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_bool():
    class FooSpider(Spider):
        name = "foo"
        crawlera_fetch_enabled = False

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_int():
    class FooSpider(Spider):
        name = "foo"
        crawlera_fetch_enabled = 0

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_str():
    class FooSpider(Spider):
        name = "foo"
        crawlera_fetch_enabled = "False"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_override():
    class FooSpider(Spider):
        name = "foo"
        crawlera_fetch_enabled = False

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(FooSpider, settings_dict={"CRAWLERA_FETCH_ENABLED": True})
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_no_apikey():
    class FooSpider(Spider):
        name = "foo"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(settings_dict={"CRAWLERA_FETCH_ENABLED": True})
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_config_values():
    FooSpider = type("FooSpider", (Spider,), {"name": "foo"})
    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider, settings_dict=SETTINGS)
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)

    assert middleware.apikey == SETTINGS["CRAWLERA_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["CRAWLERA_FETCH_URL"]
    assert middleware.apipass == SETTINGS["CRAWLERA_FETCH_APIPASS"]


def test_config_without_apipass():
    settings = SETTINGS.copy()
    settings.pop("CRAWLERA_FETCH_APIPASS", None)

    FooSpider = type("FooSpider", (Spider,), {"name": "foo"})
    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider, settings_dict=settings)
    middleware = CrawleraFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)

    assert middleware.apikey == SETTINGS["CRAWLERA_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["CRAWLERA_FETCH_URL"]
    assert middleware.apipass == ""
