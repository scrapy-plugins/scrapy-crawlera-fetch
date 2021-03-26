from scrapy import Spider
from scrapy.utils.test import get_crawler

from zyte_proxy_fetch import SmartProxyManagerFetchMiddleware

from tests.data import SETTINGS


def test_disable_via_setting():
    class FooSpider(Spider):
        name = "foo"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(FooSpider, settings_dict={"ZYTE_PROXY_ENABLED": False})
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_bool():
    class FooSpider(Spider):
        name = "foo"
        zyte_proxy_fetch_enabled = False

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_int():
    class FooSpider(Spider):
        name = "foo"
        zyte_proxy_fetch_enabled = 0

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_via_spider_attribute_str():
    class FooSpider(Spider):
        name = "foo"
        zyte_proxy_fetch_enabled = "False"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_disable_override():
    class FooSpider(Spider):
        name = "foo"
        zyte_proxy_fetch_enabled = False

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(FooSpider, settings_dict={"ZYTE_PROXY_ENABLED": True})
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_no_apikey():
    class FooSpider(Spider):
        name = "foo"

    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(settings_dict={"ZYTE_PROXY_ENABLED": True})
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)
    assert not middleware.enabled


def test_config_values():
    FooSpider = type("FooSpider", (Spider,), {"name": "foo"})
    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider, settings_dict=SETTINGS)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)

    assert middleware.apikey == SETTINGS["ZYTE_PROXY_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["ZYTE_PROXY_FETCH_URL"]
    assert middleware.apipass == SETTINGS["ZYTE_PROXY_FETCH_APIPASS"]


def test_config_without_apipass():
    settings = SETTINGS.copy()
    settings.pop("ZYTE_PROXY_FETCH_APIPASS", None)

    FooSpider = type("FooSpider", (Spider,), {"name": "foo"})
    foo_spider = FooSpider()
    foo_spider.crawler = get_crawler(spidercls=FooSpider, settings_dict=settings)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(foo_spider.crawler)
    middleware.spider_opened(foo_spider)

    assert middleware.apikey == SETTINGS["ZYTE_PROXY_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["ZYTE_PROXY_FETCH_URL"]
    assert middleware.apipass == ""
