from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

import app.repositories.transaction_metrics as repo
from app.errors.transaction_metrics import TransactionMetricsPeriodError


def test_get_period_date_range_week_ok():
    key = repo.PeriodKey(period_type="week", year=2026, week=1)
    start, end = repo.get_period_date_range(key)
    assert (end - start).days == 6


def test_get_period_date_range_week_requires_week():
    key = repo.PeriodKey(period_type="week", year=2026, week=None)
    with pytest.raises(TransactionMetricsPeriodError):
        repo.get_period_date_range(key)


def test_get_period_date_range_month_requires_month():
    key = repo.PeriodKey(period_type="month", year=2026, month=None)
    with pytest.raises(TransactionMetricsPeriodError):
        repo.get_period_date_range(key)


def test_get_period_date_range_unknown_type():
    key = repo.PeriodKey(period_type="nope", year=2026)
    with pytest.raises(TransactionMetricsPeriodError):
        repo.get_period_date_range(key)


def test_get_affected_periods():
    dt = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)
    periods = repo.get_affected_periods(dt)
    assert {p.period_type for p in periods} == {"week", "month", "year"}


def test_weeks_for_period_branches():
    assert repo._weeks_for_period("week", 2026, 1) == 1
    assert repo._weeks_for_period("month", 2026, 1) >= 4
    assert repo._weeks_for_period("year", 2026, None) in (52, 53)

    with pytest.raises(TransactionMetricsPeriodError):
        repo._weeks_for_period("bad", 2026, 1)


def test_calculate_weekly_averages_and_ratio():
    avg_income, avg_expense = repo._calculate_weekly_averages(
        total_income=Decimal("200.00"),
        total_expense=Decimal("50.00"),
        weeks=4,
    )
    assert avg_income == Decimal("50.00")
    assert avg_expense == Decimal("12.50")

    assert repo._calculate_income_expense_ratio(Decimal("10.00"), Decimal("0.00")) == Decimal("0.00")
    assert repo._calculate_income_expense_ratio(Decimal("200.00"), Decimal("50.00")) == Decimal("4.00")


def test_format_payment_method_breakdown():
    breakdown = repo.format_payment_method_breakdown({"cash": Decimal("100.00"), "transfer": Decimal("300.00")})
    assert breakdown["amounts"]["cash"] == 100.0
    assert breakdown["percentages"]["cash"] == 25.0


def test_recalc_period_orchestration(monkeypatch):
    session = MagicMock()

    monkeypatch.setattr(repo, "_fetch_period_totals", lambda _s, _f: (Decimal("200.00"), Decimal("50.00"), 3))
    monkeypatch.setattr(repo, "_fetch_payment_breakdown", lambda _s, _f: {"amounts": {}, "percentages": {}})
    monkeypatch.setattr(repo, "_weeks_for_period", lambda _pt, _y, _m: 4)

    upsert_spy = MagicMock()
    monkeypatch.setattr(repo, "_upsert_metrics", upsert_spy)

    repo.recalc_period(session, period_type="month", year=2026, month=1, week=None)

    assert upsert_spy.call_count == 1
    kwargs = upsert_spy.call_args.kwargs
    assert kwargs["balance"] == Decimal("150.00")
    assert kwargs["weekly_average_income"] == Decimal("50.00")
