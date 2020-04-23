from typing import Type, TypeVar

from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.spiders import Spider


FetchMiddlewareTV = TypeVar("FetchMiddlewareTV", bound="SimpleFetchMiddleware")


class SimpleFetchMiddleware:
    def __init__(self, crawler: Crawler) -> None:
        self.crawler = crawler
        if not crawler.settings.getbool("SIMPLE_FETCH_ENABLED"):
            raise NotConfigured()

    @classmethod
    def from_crawler(cls: Type[FetchMiddlewareTV], crawler: Crawler) -> FetchMiddlewareTV:
        return cls(crawler)

    def process_request(self, request: Request, spider: Spider) -> None:
        return None

    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        return response
