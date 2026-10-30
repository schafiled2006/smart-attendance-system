"""Utility helpers: digits, Tehran time, Jalali dates and logging."""
from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

import jdatetime

from backend import config

_PERSIAN_ZERO = 0x06F0
_ARABIC_ZERO = 0x0660
_DIGIT_TRANSLATION: dict[int, str] = {}
for _digit in range(10):
    _DIGIT_TRANSLATION[_PERSIAN_ZERO + _digit] = str(_digit)
    _DIGIT_TRANSLATION[_ARABIC_ZERO + _digit] = str(_digit)

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOG_FILES: set[str] = set()


def _tehran() -> ZoneInfo:
    """Return the configured timezone, read from config at call time.

    Section 4 of PROJECT_CONTEXT.md requires every module to read settings
    as ``config.NAME`` at call time so tests can monkeypatch them.
    """
    return ZoneInfo(config.TIMEZONE)


def normalize_digits(text: str) -> str:
    """Convert Persian and Arabic-Indic digits to ASCII digits."""
    return text.translate(_DIGIT_TRANSLATION)


def now_tehran() -> datetime:
    """Return the current timezone-aware time in Asia/Tehran."""
    return datetime.now(_tehran())


def to_iso(dt: datetime) -> str:
    """Serialize a datetime as ISO 8601 in Asia/Tehran, without microseconds."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    return dt.astimezone(_tehran()).isoformat(timespec="seconds")


def parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string into an aware Asia/Tehran datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    return dt.astimezone(_tehran())


def to_jalali_str(dt_or_iso: datetime | str, with_time: bool = False) -> str:
    """Format a datetime (or ISO string) as a Jalali date with ASCII digits."""
    dt = parse_iso(dt_or_iso) if isinstance(dt_or_iso, str) else dt_or_iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tehran())
    jalali = jdatetime.datetime.fromgregorian(datetime=dt.astimezone(_tehran()))
    result = f"{jalali.year:04d}/{jalali.month:02d}/{jalali.day:02d}"
    if with_time:
        result += f" {jalali.hour:02d}:{jalali.minute:02d}"
    return result


def setup_logging() -> None:
    """Configure a rotating UTF-8 file logger on logs/app.log.

    Calling this function again for the same log file is a no-op, so repeated
    imports do not add duplicate handlers.
    """
    log_file = Path(config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    key = str(log_file.resolve())
    if key in _LOG_FILES:
        return

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    _LOG_FILES.add(key)
