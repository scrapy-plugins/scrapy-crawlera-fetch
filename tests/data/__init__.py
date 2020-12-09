from scrapy import Spider


class DummySpider(Spider):
    name = "dummy"

    def parse(self, response):
        pass


dummy_spider = DummySpider()


SETTINGS = {
    "CRAWLERA_FETCH_ENABLED": True,
    "CRAWLERA_FETCH_URL": "https://example.org",
    "CRAWLERA_FETCH_APIKEY": "secret-key",
}
