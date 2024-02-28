import base64
import binascii
import json
import logging
import os
import time
from enum import Enum
from typing import Optional, Type, TypeVar

import scrapy
from scrapy.crawler import Crawler
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.responsetypes import responsetypes
from scrapy.settings import BaseSettings
from scrapy.http import Headers
from scrapy.spiders import Spider
from scrapy.statscollectors import StatsCollector
from scrapy.utils.request import request_from_dict
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
    url = "http://fetch.crawlera.com:8010/fetch/v2/"
    apikey = ""
    enabled = False

    crawler = None  # type: Crawler
    stats = None  # type: StatsCollector
    total_latency = None  # type: int

    @classmethod
    def from_crawler(cls: Type[MiddlewareTypeVar], crawler: Crawler) -> MiddlewareTypeVar:
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=scrapy.signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=scrapy.signals.spider_closed)
        middleware.crawler = crawler
        middleware.stats = crawler.stats
        middleware.total_latency = 0
        return middleware

    def _read_settings(self, spider: Spider) -> None:
        settings = spider.crawler.settings
        apikey = getattr(spider, "crawlera_fetch_apikey", settings.get("CRAWLERA_FETCH_APIKEY"))
        if not apikey:
            self.enabled = False
            logger.info("Crawlera Fetch API cannot be used without an apikey")
            return

        self.apikey = apikey
        self.apipass = getattr(spider, "crawlera_fetch_apipass", settings.get("CRAWLERA_FETCH_APIPASS", ""))
        self.auth_header = basic_auth_header(self.apikey, self.apipass)

        if url := getattr(spider, "crawlera_fetch_url", settings.get("CRAWLERA_FETCH_URL")):
            self.url = url

        self.download_slot_policy = settings.get(
            "CRAWLERA_FETCH_DOWNLOAD_SLOT_POLICY", DownloadSlotPolicy.Domain
        )

        self.raise_on_error = settings.getbool("CRAWLERA_FETCH_RAISE_ON_ERROR", True)

        self.default_args = settings.getdict("CRAWLERA_FETCH_DEFAULT_ARGS", {})

    def spider_opened(self, spider):
        try:
            spider_attr = getattr(spider, "crawlera_fetch_enabled")
        except AttributeError:
            if not spider.crawler.settings.getbool("CRAWLERA_FETCH_ENABLED"):
                self.enabled = False
                logger.info("Crawlera Fetch disabled (CRAWLERA_FETCH_ENABLED setting)")
                return
        else:
            if not BaseSettings({"enabled": spider_attr}).getbool("enabled"):
                self.enabled = False
                logger.info("Crawlera Fetch disabled (crawlera_fetch_enabled spider attribute)")
                return

        self.enabled = True
        self._read_settings(spider)
        if self.enabled:
            logger.info(
                "Using Crawlera Fetch API at %s with apikey %s***" % (self.url, self.apikey[:5])
            )

    def spider_closed(self, spider: Spider, reason: str) -> None:
        if self.enabled:
            self.stats.set_value("crawlera_fetch/total_latency", self.total_latency)
            response_count = self.stats.get_value("crawlera_fetch/response_count")
            if response_count:
                avg_latency = self.total_latency / response_count
                self.stats.set_value("crawlera_fetch/avg_latency", avg_latency)

    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        if not self.enabled:
            return None

        try:
            crawlera_meta = request.meta[META_KEY]
        except KeyError:
            crawlera_meta = {}

        if crawlera_meta.get("skip") or crawlera_meta.get("original_request"):
            return None

        self._set_download_slot(request, spider)

        self.stats.inc_value("crawlera_fetch/request_count")
        self.stats.inc_value("crawlera_fetch/request_method_count/{}".format(request.method))

        shub_jobkey = os.environ.get("SHUB_JOBKEY")
        if shub_jobkey:
            self.default_args["job_id"] = shub_jobkey

        body = {"url": request.url}

        # assemble JSON payload
        original_body_text = request.body.decode(request.encoding)
        if original_body_text:
            body["body"] = original_body_text
        if request.method != "GET":
            body["method"] = request.method
        body.update(self.default_args)
        body.update(crawlera_meta.get("args") or {})
        body_json = json.dumps(body)

        additional_meta = {
            "original_request": request.to_dict(),
            "timing": {"start_ts": time.time()},
        }
        crawlera_meta.update(additional_meta)

        additional_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.apikey:
            additional_headers["Authorization"] = self.auth_header
        request.headers.update(additional_headers)

        if shub_jobkey:
            request.headers["X-Crawlera-JobId"] = shub_jobkey

        if scrapy.version_info < (2, 0, 0):
            original_url_flag = "original url: {}".format(request.url)
            if original_url_flag not in request.flags:
                request.flags.append(original_url_flag)

        request.meta[META_KEY] = crawlera_meta
        return request.replace(url=self.url, method="POST", body=body_json)

    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        if not self.enabled:
            return response

        try:
            crawlera_meta = request.meta[META_KEY]
        except KeyError:
            crawlera_meta = {}

        if crawlera_meta.get("skip") or not crawlera_meta.get("original_request"):
            return response

        original_request = request_from_dict(crawlera_meta["original_request"], spider=spider)

        self.stats.inc_value("crawlera_fetch/response_count")
        self._calculate_latency(request)

        self.stats.inc_value("crawlera_fetch/api_status_count/{}".format(response.status))

        if response.headers.get("X-Crawlera-Error"):
            message = response.headers["X-Crawlera-Error"].decode("utf8")
            self.stats.inc_value("crawlera_fetch/response_error")
            self.stats.inc_value("crawlera_fetch/response_error/{}".format(message))
            log_msg = "Error downloading <{} {}> (status: {}, X-Crawlera-Error header: {})"
            log_msg = log_msg.format(
                original_request.method,
                original_request.url,
                response.status,
                message,
            )
            if self.raise_on_error:
                raise CrawleraFetchException(log_msg)
            else:
                logger.warning(log_msg)
                return response

        try:
            json_response = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.stats.inc_value("crawlera_fetch/response_error")
            self.stats.inc_value("crawlera_fetch/response_error/JSONDecodeError")
            log_msg = "Error decoding <{} {}> (status: {}, message: {}, lineno: {}, colno: {})"
            log_msg = log_msg.format(
                original_request.method,
                original_request.url,
                response.status,
                exc.msg,
                exc.lineno,
                exc.colno,
            )
            if self.raise_on_error:
                raise CrawleraFetchException(log_msg) from exc
            else:
                logger.warning(log_msg)
                return response

        server_error = json_response.get("crawlera_error") or json_response.get("error_code")
        original_status = json_response.get("original_status")
        request_id = json_response.get("id") or json_response.get("uncork_id")
        if server_error:
            message = json_response.get("body") or json_response.get("message")
            self.stats.inc_value("crawlera_fetch/response_error")
            self.stats.inc_value("crawlera_fetch/response_error/{}".format(server_error))
            log_msg = (
                "Error downloading <{} {}> (Original status: {}, "
                "Fetch API error message: {}, Request ID: {})"
            )
            log_msg = log_msg.format(
                original_request.method,
                original_request.url,
                original_status or "unknown",
                message,
                request_id or "unknown",
            )
            if self.raise_on_error:
                raise CrawleraFetchException(log_msg)
            else:
                logger.warning(log_msg)
                return response

        self.stats.inc_value("crawlera_fetch/response_status_count/{}".format(original_status))

        crawlera_meta["upstream_response"] = {
            "status": response.status,
            "headers": response.headers,
            "body": json_response,
        }
        if not json_response.get("body"):
            return response
        try:
            resp_body = base64.b64decode(json_response["body"], validate=True)
        except (binascii.Error, ValueError, TypeError):
            resp_body = json_response["body"]
        if isinstance(json_response["headers"], dict):
            headers = Headers(json_response["headers"])
        else:
            headers = Headers({x["name"]: x["value"] for x in json_response["headers"]})
        headers.pop(b"Content-Encoding", None)
        respcls = responsetypes.from_args(
            headers=headers,
            url=json_response["url"],
            body=resp_body,
        )
        return response.replace(
            cls=respcls,
            request=original_request,
            headers=headers,
            url=json_response["url"],
            body=resp_body,
            status=original_status or 200,
            encoding='utf-8'  # Need to test more
        )

    def _set_download_slot(self, request: Request, spider: Spider) -> None:
        if self.download_slot_policy == DownloadSlotPolicy.Domain:
            slot = self.crawler.engine.downloader._get_slot_key(request, spider)
            request.meta["download_slot"] = slot
        elif self.download_slot_policy == DownloadSlotPolicy.Single:
            request.meta["download_slot"] = "__crawlera_fetch__"
        # Otherwise use Scrapy default policy

    def _calculate_latency(self, request: Request) -> None:
        timing = request.meta[META_KEY]["timing"]
        timing["end_ts"] = time.time()
        timing["latency"] = timing["end_ts"] - timing["start_ts"]
        self.total_latency += timing["latency"]
        max_latency = max(self.stats.get_value("crawlera_fetch/max_latency", 0), timing["latency"])
        self.stats.set_value("crawlera_fetch/max_latency", max_latency)
