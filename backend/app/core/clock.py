"""All time reads go through now(). Offset (seconds) is persisted in system_config."""
from datetime import UTC, datetime, timedelta

_offset = timedelta(0)
_fixed: datetime | None = None  # tests


def now() -> datetime:
    return _fixed if _fixed else datetime.now(UTC) + _offset


def set_offset(seconds: float) -> None:
    global _offset
    _offset = timedelta(seconds=seconds)


def get_offset_seconds() -> float:
    return _offset.total_seconds()


def set_fixed(dt: datetime | None) -> None:
    global _fixed
    _fixed = dt
