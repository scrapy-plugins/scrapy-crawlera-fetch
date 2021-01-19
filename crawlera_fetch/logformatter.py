import json
from contextlib import suppress
from typing import Optional

from scrapy.http.request import Request
from scrapy.http.response import Response
from scrapy.logformatter import LogFormatter
from scrapy.spiders import Spider
from twisted.python.failure import Failure


class CrawleraFetchLogFormatter(LogFormatter):
    """
    Since the CrawleraFetchMiddleware sets a new URL for outgoing requests, by
    default the URLs shown in the logs are not the original ones. By enabling
    this formatter, this behaviour is reverted.

    For instance, instead of:
        DEBUG: Crawled (200) <POST https://api.crawlera.com/fetch/v2> (referer: None)

    this formatter shows:
        DEBUG: Crawled (200) <GET https://example.org> (referer: None)
    """

    def _set_target_url(self, result: dict, request: Request) -> dict:
        with suppress(json.decoder.JSONDecodeError):
            payload = json.loads(request.body.decode(request.encoding))
            result["args"]["request"] = "<%s %s>" % (payload.get("method", "GET"), payload["url"])
        return result

    def crawled(self, request: Request, response: Response, spider: Spider) -> dict:
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).crawled(request, response, spider),
            request=request,
        )

    def spider_error(
        self, failure: Failure, request: Request, response: Response, spider: Spider
    ) -> dict:
        """
        Only available in Scrapy 2.0+
        """
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).spider_error(
                failure, request, response, spider
            ),
            request=request,
        )

    def download_error(
        self, failure: Failure, request: Request, spider: Spider, errmsg: Optional[str] = None
    ) -> dict:
        """
        Only available in Scrapy 2.0+
        """
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).download_error(
                failure, request, spider, errmsg
            ),
            request=request,
        )
