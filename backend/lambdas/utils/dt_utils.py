import logging as log
import time
from datetime import datetime, timezone, date

from dateutil import parser


def parse_iso(value: str) -> datetime:
    if value:
        return parser.isoparse(value)
    return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def date_to_iso(date_obj) -> str:
    if isinstance(date_obj, date):
        return date_obj.isoformat()
    return date_obj.date().isoformat()


def timestamp_to_iso(utc_timestamp: datetime) -> str:
    if utc_timestamp is None:
        return None

    if utc_timestamp.tzinfo:
        return utc_timestamp.isoformat()

    return utc_timestamp.isoformat() + "+00:00"


def datetime_from_millis(millis, tz=None) -> datetime:
    if not millis:
        return None
    if not tz:
        tz = timezone.utc
    return datetime.fromtimestamp(float(millis) / 1000, tz)


class Timer:
    def __init__(self, level=log.DEBUG):
        self.level = level
        self.timer_start = None
        self.timer_stop = None
        self.message = None

    def start(self, message: str = 'Operation'):
        self.message = message
        self.timer_start = time.perf_counter()

    def stop(self, write_log: bool = True):
        self.timer_stop = time.perf_counter()
        if write_log:
            log.log(self.level, "%s took %s seconds", self.message, self.timer_stop - self.timer_start)
