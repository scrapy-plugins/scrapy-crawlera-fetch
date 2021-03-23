import pytest
from scrapy.exceptions import NotConfigured
from scrapy.utils.test import get_crawler

from zyte_proxy_fetch import SmartProxyManagerFetchMiddleware

from tests.data import SETTINGS


def test_not_enabled():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"ZYTE_PROXY_FETCH_ENABLED": False})
        SmartProxyManagerFetchMiddleware.from_crawler(crawler)


def test_no_apikey():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"ZYTE_PROXY_FETCH_ENABLED": True})
        SmartProxyManagerFetchMiddleware.from_crawler(crawler)


def test_config_values():
    crawler = get_crawler(settings_dict=SETTINGS)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(crawler)

    assert middleware.apikey == SETTINGS["ZYTE_PROXY_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["ZYTE_PROXY_FETCH_URL"]
    assert middleware.apipass == SETTINGS["ZYTE_PROXY_FETCH_APIPASS"]


def test_config_without_apipass():
    s = SETTINGS.copy()
    s.pop("ZYTE_PROXY_FETCH_APIPASS", None)
    crawler = get_crawler(settings_dict=s)
    middleware = SmartProxyManagerFetchMiddleware.from_crawler(crawler)

    assert middleware.apikey == SETTINGS["ZYTE_PROXY_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["ZYTE_PROXY_FETCH_URL"]
    assert middleware.apipass == ""
