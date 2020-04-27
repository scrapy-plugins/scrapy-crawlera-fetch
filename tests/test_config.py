import pytest
from scrapy.exceptions import NotConfigured
from scrapy.utils.test import get_crawler

from crawlera_fetch_middleware import CrawleraFetchMiddleware

from tests.data import SETTINGS


def test_not_enabled():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"CRAWLERA_ENABLED": False})
        CrawleraFetchMiddleware.from_crawler(crawler)


def test_no_apikey():
    with pytest.raises(NotConfigured):
        crawler = get_crawler(settings_dict={"CRAWLERA_ENABLED": True})
        CrawleraFetchMiddleware.from_crawler(crawler)


def test_config_values():
    crawler = get_crawler(settings_dict=SETTINGS)
    middleware = CrawleraFetchMiddleware.from_crawler(crawler)

    assert middleware.apikey == SETTINGS["CRAWLERA_APIKEY"]
    assert middleware.url == SETTINGS["CRAWLERA_URL"]
