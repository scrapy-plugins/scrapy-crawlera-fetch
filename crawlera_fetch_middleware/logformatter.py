import json

from scrapy.logformatter import LogFormatter


# py2 compatibility
try:
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


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

    def _set_target_url(self, result, request):
        try:
            payload = json.loads(request.body.decode(request.encoding))
            result["args"]["request"] = "<%s %s>" % (payload["method"], payload["url"])
        except JSONDecodeError:
            pass
        return result

    def crawled(self, request, response, spider):
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).crawled(request, response, spider),
            request=request,
        )

    def spider_error(self, failure, request, response, spider):
        """
        Only available in Scrapy 2.0+
        """
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).spider_error(
                failure, request, response, spider
            ),
            request=request,
        )

    def download_error(self, failure, request, spider, errmsg=None):
        """
        Only available in Scrapy 2.0+
        """
        return self._set_target_url(
            result=super(CrawleraFetchLogFormatter, self).download_error(
                failure, request, spider, errmsg
            ),
            request=request,
        )
