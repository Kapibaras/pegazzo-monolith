from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.config.constants import EXPIRING_SOON_DAYS
from app.enum.crm import DocumentExpiryStatus


def compute_expiry_status(expiry_date, now: datetime | None = None) -> DocumentExpiryStatus | None:
    """Return valid / expiring_soon / expired based on expiry_date, or None if no expiry."""
    if expiry_date is None:
        return None
    if now is None:
        now = datetime.now(UTC)
    if now > expiry_date:
        return DocumentExpiryStatus.EXPIRED
    if now + timedelta(days=EXPIRING_SOON_DAYS) > expiry_date:
        return DocumentExpiryStatus.EXPIRING_SOON
    return DocumentExpiryStatus.VALID


def start_of_month(year: int, month: int) -> date:
    """Return first day of month."""
    return date(year, month, 1)


def end_of_month(year: int, month: int) -> date:
    """Return last day of month."""
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def start_of_year(year: int) -> date:
    """Return first day of year."""
    return date(year, 1, 1)


def end_of_year(year: int) -> date:
    """Return last day of year."""
    return date(year, 12, 31)


def iso_weeks_in_year(year: int) -> int:
    """ISO weeks in a year (Dec 28 is always in the last ISO week)."""
    return date(year, 12, 28).isocalendar().week


def count_iso_weeks_in_month(year: int, month: int) -> int:
    """Return the number of ISO weeks overlapping a given month."""
    start = start_of_month(year, month)
    end = end_of_month(year, month)

    start_iso = start.isocalendar()
    end_iso = end.isocalendar()

    start_week = start_iso.week
    end_week = end_iso.week

    if end_iso.year > start_iso.year:
        return (iso_weeks_in_year(start_iso.year) - start_week + 1) + end_week

    return max(1, end_week - start_week + 1)
