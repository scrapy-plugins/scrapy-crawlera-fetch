# Scrapy Middleware for Zyte Smart Proxy Manager Simple Fetch API
[![actions](https://github.com/scrapy-plugins/scrapy-zyte-proxy-fetch/workflows/Build/badge.svg)](https://github.com/scrapy-plugins/scrapy-zyte-proxy-fetch/actions)
[![codecov](https://codecov.io/gh/scrapy-plugins/scrapy-zyte-proxy-fetch/branch/master/graph/badge.svg)](https://codecov.io/gh/scrapy-plugins/scrapy-zyte-proxy-fetch)

This package provides a Scrapy
[Downloader Middleware](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html)
to transparently interact with the
[Zyte Smart Proxy Manager Fetch API](https://docs.zyte.com/smart-proxy-manager/fetch-api.html).


## Requirements

* Python 3.5+
* Scrapy 1.6+


## Installation

Not yet available on PyPI. However, it can be installed directly from GitHub:

`pip install git+ssh://git@github.com/scrapy-plugins/scrapy-zyte-proxy-fetch.git`

or

`pip install git+https://github.com/scrapy-plugins/scrapy-zyte-proxy-fetch.git`


## Configuration

Enable the `SmartProxyManagerFetchMiddleware` via the
[`DOWNLOADER_MIDDLEWARES`](https://docs.scrapy.org/en/latest/topics/settings.html#downloader-middlewares)
setting:

```
DOWNLOADER_MIDDLEWARES = {
    "zyte_proxy_fetch.SmartProxyManagerFetchMiddleware": 585,
}
```

Please note that the middleware needs to be placed before the built-in `HttpCompressionMiddleware`
middleware (which has a priority of 590), otherwise incoming responses will be compressed and the
Smart Proxy Manager middleware won't be able to handle them.

### Settings

* `ZYTE_PROXY_FETCH_ENABLED` (type `bool`, default `False`). Whether or not the middleware will be enabled,
    i.e. requests should be downloaded using the Smart Proxy Manager Fetch API

* `ZYTE_PROXY_FETCH_APIKEY` (type `str`). API key to be used to authenticate against the Smart Proxy Manager endpoint
    (mandatory if enabled)

* `ZYTE_PROXY_FETCH_URL` (Type `str`, default `"http://fetch.crawlera.com:8010/fetch/v2/"`).
    The endpoint of a specific Smart Proxy Manager instance

* `ZYTE_PROXY_FETCH_RAISE_ON_ERROR` (type `bool`, default `True`). Whether or not the middleware will
    raise an exception if an error occurs while downloading or decoding a request. If `False`, a
    warning will be logged and the raw upstream response will be returned upon encountering an error.

* `ZYTE_PROXY_FETCH_DOWNLOAD_SLOT_POLICY` (type `enum.Enum` - `zyte_proxy_fetch.DownloadSlotPolicy`,
    default `DownloadSlotPolicy.Domain`).
    Possible values are `DownloadSlotPolicy.Domain`, `DownloadSlotPolicy.Single`,
    `DownloadSlotPolicydefault` (Scrapy default). If set to `DownloadSlotPolicy.Domain`, please
    consider setting `SCHEDULER_PRIORITY_QUEUE="scrapy.pqueues.DownloaderAwarePriorityQueue"` to
    make better usage of concurrency options and avoid delays.

* `ZYTE_PROXY_FETCH_DEFAULT_ARGS` (type `dict`, default `{}`)
    Default values to be sent to the Smart Proxy Manager Fetch API. For instance, set to `{"device": "mobile"}`
    to render all requests with a mobile profile.

### Log formatter

Since the URL for outgoing requests is modified by the middleware, by default the logs will show
the URL for the Smart Proxy Manager endpoint. To revert this behaviour you can enable the provided
log formatter by overriding the [`LOG_FORMATTER`](https://docs.scrapy.org/en/latest/topics/settings.html#log-formatter)
setting:

```
LOG_FORMATTER = "zyte_proxy_fetch.SmartProxyManagerLogFormatter"
```

Note that the ability to override the error messages for spider and download errors was added
in Scrapy 2.0. When using a previous version, the middleware will add the original request URL
to the `Request.flags` attribute, which is shown in the logs by default.


## Usage

If the middleware is enabled, by default all requests will be redirected to the specified
Smart Proxy Manager Fetch endpoint, and modified to comply with the format expected by the Smart Proxy Manager Fetch API.
The three basic processed arguments are `method`, `url` and `body`.
For instance, the following request:

```python
Request(url="https://httpbin.org/post", method="POST", body="foo=bar")
```

will be converted to:

```python
Request(url="<Smart Proxy Manager Fetch API endpoint>", method="POST",
        body='{"url": "https://httpbin.org/post", "method": "POST", "body": "foo=bar"}',
        headers={"Authorization": "Basic <derived from APIKEY>",
                 "Content-Type": "application/json",
                 "Accept": "application/json"})
```

### Additional arguments

Additional arguments could be specified under the `zyte_proxy_fetch.args` `Request.meta` key. For instance:

```python
Request(
    url="https://example.org",
    meta={"zyte_proxy_fetch": {"args": {"region": "us", "device": "mobile"}}},
)
```

is translated into the following body:

```python
'{"url": "https://example.org", "method": "GET", "body": "", "region": "us", "device": "mobile"}'
```

Arguments set for a specific request through the `zyte_proxy_fetch.args` key override those
set with the `ZYTE_PROXY_FETCH_DEFAULT_ARGS` setting.

### Accessing original request and raw Zyte Smart Proxy Manager response

The `url`, `method`, `headers` and `body` attributes of the original request are available under
the `zyte_proxy_fetch.original_request` `Response.meta` key.

The `status`, `headers` and `body` attributes of the upstream Smart Proxy Manager response are available under
the `zyte_proxy_fetch.upstream_response` `Response.meta` key.

### Skipping requests

You can instruct the middleware to skip a specific request by setting the `zyte_proxy_fetch.skip`
[Request.meta](https://docs.scrapy.org/en/latest/topics/request-response.html#scrapy.http.Request.meta)
key:

```python
Request(
    url="https://example.org",
    meta={"zyte_proxy_fetch": {"skip": True}},
)
```
