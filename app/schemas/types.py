from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime


def _normalize_to_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


RequestUTCDatetime = Annotated[AwareDatetime, AfterValidator(_normalize_to_utc)]
"""Pydantic type for request schemas datetime fields.

Enforces timezone-aware input (rejects naive datetimes) and normalizes
any timezone to UTC before the value reaches the service layer.

Use this on any datetime field that comes from client requests, not on response schemas.
"""
