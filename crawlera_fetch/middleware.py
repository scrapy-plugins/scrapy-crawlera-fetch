import json
import logging
from typing import Optional, Type, TypeVar

from scrapy import version_info as scrapy_version
from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.responsetypes import responsetypes
from scrapy.spiders import Spider
from w3lib.http import basic_auth_header


logger = logging.getLogger("crawlera-fetch-middleware")


MiddlewareTypeVar = TypeVar("MiddlewareTypeVar", bound="CrawleraFetchMiddleware")


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

        logger.debug(
            "Using Crawlera Fetch API at %s with apikey %s***" % (self.url, self.apikey[:5])
        )

    @classmethod
    def from_crawler(cls: Type[MiddlewareTypeVar], crawler: Crawler) -> MiddlewareTypeVar:
        return cls(crawler)

    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        skip = request.meta.get("crawlera_fetch_skip")
        processed = request.meta.get("crawlera_fetch_original_request")
        if skip or processed:
            return None

        request.meta["crawlera_fetch_original_request"] = {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "body": request.body,
        }

        # assemble JSON payload
        original_body_text = request.body.decode(request.encoding)
        body = {"url": request.url, "method": request.method, "body": original_body_text}
        body.update(request.meta.get("crawlera_fetch") or {})
        body_json = json.dumps(body)

        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        request.headers.update(headers)

        if scrapy_version < (2, 0, 0):
            request.flags.append("Original URL: {}".format(request.url))

        return request.replace(url=self.url, method="POST", body=body_json)

    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        if request.meta.get("crawlera_fetch_skip"):
            return response

        if response.headers.get("X-Crawlera-Error"):
            logger.error(
                "Error downloading <%s %s> (status: %i, X-Crawlera-Error header: %s)",
                request.meta["crawlera_fetch_original_request"]["method"],
                request.meta["crawlera_fetch_original_request"]["url"],
                response.status,
                response.headers["X-Crawlera-Error"].decode("utf8"),
            )
            return response

        json_response = json.loads(response.text)
        request.meta["crawlera_fetch_response"] = {
            "status": response.status,
            "headers": response.headers,
            "body": json_response,
        }
        respcls = responsetypes.from_args(
            headers=json_response["headers"], url=json_response["url"], body=json_response["body"],
        )
        return response.replace(
            cls=respcls,
            headers=json_response["headers"],
            url=json_response["url"],
            body=json_response["body"],
            status=json_response["original_status"],
        )
