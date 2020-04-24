import json

from scrapy.exceptions import NotConfigured
from w3lib.http import basic_auth_header


class CrawleraSimpleFetchMiddleware:

    url = "https://api.crawlera.com/fetch/v2"
    apikey = ""

    def __init__(self, crawler):
        if not crawler.settings.getbool("CRAWLERA_ENABLED"):
            raise NotConfigured()
        elif not crawler.settings.get("CRAWLERA_APIKEY"):
            raise NotConfigured("Crawlera cannot be used without an apikey")
        else:
            self.auth_header = basic_auth_header(crawler.settings["CRAWLERA_APIKEY"], "")

        if crawler.settings.get("CRAWLERA_URL"):
            self.url = crawler.settings["CRAWLERA_URL"]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        crawlera_meta = request.meta.get("crawlera") or {}
        original_body_text = request.body.decode(request.encoding)
        body = {"url": request.url, "method": request.method, "body": original_body_text}
        body.update(crawlera_meta)

        headers = request.headers
        headers.update({"Authorization": self.auth_header, "Content-Type": "application/json"})

        return request.replace(
            url=self.url, method="POST", headers=headers, body=json.dumps(body),
        )

    def process_response(self, request, response, spider):
        return response
