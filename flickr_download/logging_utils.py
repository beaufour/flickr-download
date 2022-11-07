"""Utilities for Python logger."""
import re
from logging import Formatter, LogRecord
from typing import Optional

PATTERNS = [
    (r"([?&]oauth_token=)[^&]*", r"\1***"),
    (r"([?&]oauth_consumer_key=)[^&]*", r"\1***"),
    (r"([?&]oauth_body_hash=)[^&]*", r"\1***"),
    (r"([?&]api_key=)[^&]*", r"\1***"),
]


def _redact(msg: str) -> str:
    """Redacts a list of string patters from a string."""
    for pattern in PATTERNS:
        msg = re.sub(pattern[0], pattern[1], msg)
    return msg


class APIKeysRedacter(Formatter):
    """Wraps `_redact()` into a class that can be passed to the `logging`
    framework."""

    def __init__(self, orig_formatter: Optional[Formatter]):
        Formatter.__init__(self)
        self._orig_formatter = orig_formatter

    def format(self, record: LogRecord) -> str:
        if self._orig_formatter:
            msg = self._orig_formatter.format(record)
        else:
            msg = record.getMessage()
        return _redact(msg)
