from logging import Logger
from typing import Optional, Union

from scrapy import Request, Spider
from scrapy.utils.python import global_object_name


def _get_retry_request(
    request: Request,
    *,
    spider: Spider,
    reason: Union[str, Exception] = "unspecified",
    max_retry_times: Optional[int] = None,
    priority_adjust: Optional[int] = None,
    logger: Logger,
    stats_base_key: str,
) -> Optional[Request]:
    """
    Fallback implementation, taken verbatim from https://github.com/scrapy/scrapy/pull/4902
    """
    settings = spider.crawler.settings
    stats = spider.crawler.stats
    retry_times = request.meta.get("retry_times", 0) + 1
    if max_retry_times is None:
        max_retry_times = request.meta.get("max_retry_times")
        if max_retry_times is None:
            max_retry_times = settings.getint("RETRY_TIMES")
    if retry_times <= max_retry_times:
        logger.debug(
            "Retrying %(request)s (failed %(retry_times)d times): %(reason)s",
            {"request": request, "retry_times": retry_times, "reason": reason},
            extra={"spider": spider},
        )
        new_request = request.copy()
        new_request.meta["retry_times"] = retry_times
        new_request.dont_filter = True
        if priority_adjust is None:
            priority_adjust = settings.getint("RETRY_PRIORITY_ADJUST")
        new_request.priority = request.priority + priority_adjust

        if callable(reason):
            reason = reason()
        if isinstance(reason, Exception):
            reason = global_object_name(reason.__class__)

        stats.inc_value(f"{stats_base_key}/count")
        stats.inc_value(f"{stats_base_key}/reason_count/{reason}")
        return new_request
    else:
        stats.inc_value(f"{stats_base_key}/max_reached")
        logger.error(
            "Gave up retrying %(request)s (failed %(retry_times)d times): " "%(reason)s",
            {"request": request, "retry_times": retry_times, "reason": reason},
            extra={"spider": spider},
        )
        return None
