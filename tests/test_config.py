import pytest
from scrapy.exceptions import NotConfigured
from scrapy.utils.test import get_crawler

from crawlera_fetch import CrawleraFetchMiddleware

from tests.data import SETTINGS


def test_not_enabled():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"CRAWLERA_FETCH_ENABLED": False})
        CrawleraFetchMiddleware.from_crawler(crawler)


def test_no_apikey():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"CRAWLERA_FETCH_ENABLED": True})
        CrawleraFetchMiddleware.from_crawler(crawler)


def test_config_values():
    crawler = get_crawler(settings_dict=SETTINGS)
    middleware = CrawleraFetchMiddleware.from_crawler(crawler)

    assert middleware.apikey == SETTINGS["CRAWLERA_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["CRAWLERA_FETCH_URL"]
    assert middleware.apipass == SETTINGS["CRAWLERA_FETCH_APIPASS"]


def test_config_without_apipass():
    s = SETTINGS.copy()
    s.pop("CRAWLERA_FETCH_APIPASS", None)
    crawler = get_crawler(settings_dict=s)
    middleware = CrawleraFetchMiddleware.from_crawler(crawler)

    assert middleware.apikey == SETTINGS["CRAWLERA_FETCH_APIKEY"]
    assert middleware.url == SETTINGS["CRAWLERA_FETCH_URL"]
    assert middleware.apipass == ""
