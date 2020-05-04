import json
import logging
from enum import Enum
from typing import Optional, Type, TypeVar

import scrapy
from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.responsetypes import responsetypes
from scrapy.spiders import Spider
from w3lib.http import basic_auth_header


logger = logging.getLogger("crawlera-fetch-middleware")


MiddlewareTypeVar = TypeVar("MiddlewareTypeVar", bound="CrawleraFetchMiddleware")


META_KEY = "crawlera_fetch"


class DownloadSlotPolicy(Enum):
    Domain = "domain"
    Single = "single"
    Default = "default"


class CrawleraFetchException(Exception):
    pass


class CrawleraFetchMiddleware:

    url = "https://api.crawlera.com/fetch/v2"
    apikey = ""

    def __init__(self, crawler: Crawler) -> None:
        if not crawler.settings.getbool("CRAWLERA_FETCH_ENABLED"):
            raise NotConfigured()
        elif not crawler.settings.get("CRAWLERA_FETCH_APIKEY"):
            raise NotConfigured("Crawlera Fetch API cannot be used without an apikey")
        else:
            self.apikey = crawler.settings["CRAWLERA_FETCH_APIKEY"]
            self.auth_header = basic_auth_header(self.apikey, "")

        if crawler.settings.get("CRAWLERA_FETCH_URL"):
            self.url = crawler.settings["CRAWLERA_FETCH_URL"]

        self.download_slot_policy = crawler.settings.get(
            "CRAWLERA_FETCH_DOWNLOAD_SLOT_POLICY", DownloadSlotPolicy.Domain
        )

        self.raise_on_error = crawler.settings.getbool("CRAWLERA_FETCH_RAISE_ON_ERROR", True)

        self.crawler = crawler
        self.stats = crawler.stats

        logger.debug(
            "Using Crawlera Fetch API at %s with apikey %s***" % (self.url, self.apikey[:5])
        )

    @classmethod
    def from_crawler(cls: Type[MiddlewareTypeVar], crawler: Crawler) -> MiddlewareTypeVar:
        return cls(crawler)

    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        try:
            crawlera_meta = request.meta[META_KEY]
        except KeyError:
            crawlera_meta = {}

        if crawlera_meta.get("skip") or crawlera_meta.get("original_request"):
            return None

        self._set_download_slot(request, spider)

        self.stats.inc_value("crawlera_fetch/request_count")
        self.stats.inc_value("crawlera_fetch/request_method_count/{}".format(request.method))

        crawlera_meta["original_request"] = {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "body": request.body,
        }

        # assemble JSON payload
        original_body_text = request.body.decode(request.encoding)
        body = {"url": request.url, "method": request.method, "body": original_body_text}
        body.update(crawlera_meta.get("args") or {})
        body_json = json.dumps(body)

        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        request.headers.update(headers)

        if scrapy.version_info < (2, 0, 0):
            request.flags.append("original url: {}".format(request.url))

        return request.replace(url=self.url, method="POST", body=body_json)

    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        try:
            crawlera_meta = request.meta[META_KEY]
        except KeyError:
            crawlera_meta = {}

        if crawlera_meta.get("skip") or not crawlera_meta.get("original_request"):
            return response

        self.stats.inc_value("crawlera_fetch/response_count")

        if response.headers.get("X-Crawlera-Error"):
            message = response.headers["X-Crawlera-Error"].decode("utf8")
            self.stats.inc_value("crawlera_fetch/response_error")
            self.stats.inc_value("crawlera_fetch/response_error/{}".format(message))
            crawlera_error_args = (
                "Error downloading <%s %s> (status: %i, X-Crawlera-Error header: %s)",
                crawlera_meta["original_request"]["method"],
                crawlera_meta["original_request"]["url"],
                response.status,
                message,
            )
            if self.raise_on_error:
                raise CrawleraFetchException(*crawlera_error_args)
            else:
                logger.error(*crawlera_error_args)
                return response

        try:
            json_response = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.stats.inc_value("crawlera_fetch/response_error")
            self.stats.inc_value("crawlera_fetch/response_error/JSONDecodeError")
            json_decode_args = (
                "Error decoding <%s %s> (status: %i, message: %s, lineno: %i, colno: %i)",
                crawlera_meta["original_request"]["method"],
                crawlera_meta["original_request"]["url"],
                response.status,
                exc.msg,
                exc.lineno,
                exc.colno,
            )
            if self.raise_on_error:
                raise CrawleraFetchException(*json_decode_args)
            else:
                logger.error(*json_decode_args)
                return response

        self.stats.inc_value(
            "crawlera_fetch/response_status_count/{}".format(json_response["original_status"])
        )

        crawlera_meta["upstream_response"] = {
            "status": response.status,
            "headers": response.headers,
            "body": json_response,
        }
        respcls = responsetypes.from_args(
            headers=json_response["headers"], url=json_response["url"], body=json_response["body"],
        )
        return response.replace(
            cls=respcls,
            request=request.replace(url="https://scrapinghub.com"),
            headers=json_response["headers"],
            url=json_response["url"],
            body=json_response["body"],
            status=json_response["original_status"],
        )

    def _set_download_slot(self, request, spider):
        if self.download_slot_policy == DownloadSlotPolicy.Domain:
            slot = self.crawler.engine.downloader._get_slot_key(request, spider)
            request.meta["download_slot"] = slot
        elif self.download_slot_policy == DownloadSlotPolicy.Single:
            request.meta["download_slot"] = "__crawlera_fetch__"
        # Otherwise use Scrapy default policy
