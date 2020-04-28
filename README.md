# Scrapy Middleware for Crawlera Simple Fetch API

This package provides a Scrapy [Downloader Middleware](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html)
to transparently interact with the [Crawlera Fetch API](https://scrapinghub.atlassian.net/wiki/spaces/CRAWLERA/pages/889979197/Simple+Fetch+API).


## Installation

Work in progress - Package is currently private


## Configuration

Enable the `CrawleraFetchMiddleware` via the [`DOWNLOADER_MIDDLEWARES`](https://docs.scrapy.org/en/latest/topics/settings.html#downloader-middlewares)
setting:

```
DOWNLOADER_MIDDLEWARES = {
    "crawlera_fetch.CrawleraFetchMiddleware": 585,
}
```

Please note that the middleware needs to be placed before the built-in `HttpCompressionMiddleware`
middleware (which has a priority of 590) , otherwise incoming responses will be compressed and the
Crawlera middleware won't be able to handle them.

### Settings

* `CRAWLERA_FETCH_ENABLED` - Whether or not the middleware will be enabled,
    i.e. requests should be downloaded using the Crawlera Fetch API
* `CRAWLERA_FETCH_APIKEY` - API key to be used to authenticate against the Crawlera endpoint
    (mandatory if enabled)
* `CRAWLERA_FETCH_URL` - The endpoint of a specific Crawlera instance,
    defaults to https://api.crawlera.com/fetch/v2

### Log formatter

Since the URL for outgoing requests is modified by the middleware, by default the logs will show
the URL for the Crawlera endpoint. To revert this behaviour you can enable the provided
log formatter by overriding the [`LOG_FORMATTER`](https://docs.scrapy.org/en/latest/topics/settings.html#log-formatter)
setting:

```
LOG_FORMATTER = "crawlera_fetch.CrawleraFetchLogFormatter"
```

Note that the ability to override the error messages for spider and download errors was added
in Scrapy 2.0. When using a previous version, the middleware will add the original request URL
to the `Request.flags` attribute, which is shown in the logs by default.


## Usage

If the middleware is enabled, by default all requests will be redirected to the specified
Crawlera Fetch endpoint, and modified to comply with the format expected by the Crawlera Fetch API.
The three basic processed arguments are `method`, `url` and `body`.
For instance, the following request:

```python
Request(url="https://httpbin.org/post", method="POST", body="foo=bar")
```

will be converted to:

```python
Request(url="<Crawlera Fetch API endpoint>", method="POST",
        body='{"url": "https://httpbin.org/post", "method": "POST", "body": "foo=bar"}',
        headers={"Authorization": "Basic <derived from APIKEY>",
                 "Content-Type": "application/json",
                 "Accept": "application/json"})
```

### Additional arguments

Additional arguments could be specified under the `crawlera_fetch` Request.meta key. For instance:

```python
Request(
    url="https://example.org",
    meta={"crawlera_fetch": {"region": "us", "device": "mobile"}},
)
```

is translated into the following body:

```python
'{"url": "https://example.org", "method": "GET", "body": "", "region": "us", "device": "mobile"}'
```


### Skipping requests

You can instruct the middleware to skip a specific request by setting the `crawlera_fetch_skip`
[Request.meta](https://docs.scrapy.org/en/latest/topics/request-response.html#scrapy.http.Request.meta)
key.
