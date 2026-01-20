from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.enum.balance import Type as TxType
from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.utils.dates import (
    count_iso_weeks_in_month,
    end_of_month,
    end_of_year,
    iso_weeks_in_year,
    start_of_month,
    start_of_year,
)
from app.utils.decimal import DEC_2, calculate_percentage, round_to_2_decimals

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PeriodKey:
    """Period key."""

    period_type: str
    year: int
    month: Optional[int] = None
    week: Optional[int] = None


def get_affected_periods(dt: datetime) -> list[PeriodKey]:
    """Return affected week/month/year period keys for a datetime."""
    d = dt.date()
    iso = d.isocalendar()

    return [
        PeriodKey(period_type="week", year=iso.year, month=None, week=iso.week),
        PeriodKey(period_type="month", year=d.year, month=d.month),
        PeriodKey(period_type="year", year=d.year),
    ]


def get_period_date_range(key: PeriodKey) -> tuple[date, date]:
    """Get period date range."""
    if key.period_type == "week":
        if key.week is None:
            raise TransactionMetricsPeriodError.week_requires_week()
        start = date.fromisocalendar(key.year, key.week, 1)
        return start, start + timedelta(days=6)

    if key.period_type == "month":
        if key.month is None:
            raise TransactionMetricsPeriodError.month_requires_month()
        return start_of_month(key.year, key.month), end_of_month(key.year, key.month)

    if key.period_type == "year":
        return start_of_year(key.year), end_of_year(key.year)

    raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)


def format_payment_method_breakdown(amounts: dict[str, Decimal]) -> dict[str, Any]:
    """Format payment method breakdown."""
    total = sum(amounts.values(), Decimal("0.00"))
    return {
        "amounts": {k: float(v) for k, v in amounts.items()},
        "percentages": {k: float(calculate_percentage(v, total)) for k, v in amounts.items()},
    }


def _fetch_period_totals(session: Session, base_filter) -> tuple[Decimal, Decimal, int]:
    """Fetch period totals."""
    stmt = select(
        func.coalesce(
            func.sum(case((Transaction.type == TxType.CREDIT.value, Transaction.amount), else_=0)),
            0,
        ).label("total_income"),
        func.coalesce(
            func.sum(case((Transaction.type == TxType.DEBIT.value, Transaction.amount), else_=0)),
            0,
        ).label("total_expense"),
        func.count().label("tx_count"),
    ).where(base_filter)

    try:
        row = session.execute(stmt).one()
    except Exception:
        logger.exception("Failed fetching totals")
        raise

    return (
        round_to_2_decimals(row.total_income),
        round_to_2_decimals(row.total_expense),
        int(row.tx_count or 0),
    )


def _fetch_payment_breakdown(session: Session, base_filter) -> dict[str, Any]:
    stmt = (
        select(
            Transaction.payment_method.label("payment_method"),
            func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
        )
        .where(base_filter)
        .group_by(Transaction.payment_method)
    )

    try:
        rows = session.execute(stmt).all()
    except Exception:
        logger.exception("Failed fetching payment breakdown")
        raise

    amounts: dict[str, Decimal] = {str(r.payment_method): round_to_2_decimals(r.amount) for r in rows}
    return format_payment_method_breakdown(amounts)


def _weeks_for_period(period_type: str, year: int, month: int | None) -> int:
    if period_type == "week":
        return 1
    if period_type == "month":
        return count_iso_weeks_in_month(year, month or 1)
    if period_type == "year":
        return iso_weeks_in_year(year)
    raise TransactionMetricsPeriodError.unknown_period_type(period_type)


def _calculate_weekly_averages(
    *,
    total_income: Decimal,
    total_expense: Decimal,
    weeks: int,
) -> tuple[Decimal, Decimal]:
    w = Decimal(max(1, weeks))
    avg_income = (total_income / w).quantize(DEC_2, rounding=ROUND_HALF_UP)
    avg_expense = (total_expense / w).quantize(DEC_2, rounding=ROUND_HALF_UP)
    return avg_income, avg_expense


def _calculate_income_expense_ratio(total_income: Decimal, total_expense: Decimal) -> Decimal:
    if total_expense == 0:
        return Decimal("0.00")
    return (total_income / total_expense).quantize(DEC_2, rounding=ROUND_HALF_UP)


def _upsert_metrics(
    session: Session,
    *,
    period_type: str,
    year: int,
    month: int | None,
    week: int | None,
    total_income: Decimal,
    total_expense: Decimal,
    balance: Decimal,
    transaction_count: int,
    payment_method_breakdown: dict[str, Any],
    weekly_average_income: Decimal,
    weekly_average_expense: Decimal,
    income_expense_ratio: Decimal,
) -> None:
    stmt = insert(TransactionMetrics).values(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        transaction_count=transaction_count,
        payment_method_breakdown=payment_method_breakdown,
        weekly_average_income=weekly_average_income,
        weekly_average_expense=weekly_average_expense,
        income_expense_ratio=income_expense_ratio,
        updated_at=func.now(),
    )

    update_set = {
        "total_income": stmt.excluded.total_income,
        "total_expense": stmt.excluded.total_expense,
        "balance": stmt.excluded.balance,
        "transaction_count": stmt.excluded.transaction_count,
        "payment_method_breakdown": stmt.excluded.payment_method_breakdown,
        "weekly_average_income": stmt.excluded.weekly_average_income,
        "weekly_average_expense": stmt.excluded.weekly_average_expense,
        "income_expense_ratio": stmt.excluded.income_expense_ratio,
        "updated_at": func.now(),
    }

    if period_type == "week":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year", "week"],
            index_where=(TransactionMetrics.period_type == "week"),
            set_=update_set,
        )
    elif period_type == "month":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year", "month"],
            index_where=(TransactionMetrics.period_type == "month"),
            set_=update_set,
        )
    elif period_type == "year":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year"],
            index_where=(TransactionMetrics.period_type == "year"),
            set_=update_set,
        )
    else:
        raise TransactionMetricsPeriodError.unknown_period_type(period_type)

    try:
        session.execute(stmt)
    except Exception:
        logger.exception("Failed upserting metrics for period=%s y=%s m=%s w=%s", period_type, year, month, week)
        raise


def recalc_period(
    session: Session,
    *,
    period_type: str,
    year: int,
    month: int | None,
    week: int | None,
) -> None:
    """Recalculate metrics for a single period and UPSERT the row."""
    key = PeriodKey(period_type=period_type, year=year, month=month, week=week)
    start_d, end_d = get_period_date_range(key)

    base_filter = func.date(Transaction.date).between(start_d, end_d)

    total_income, total_expense, tx_count = _fetch_period_totals(session, base_filter)
    balance = (total_income - total_expense).quantize(DEC_2, rounding=ROUND_HALF_UP)

    breakdown = _fetch_payment_breakdown(session, base_filter)

    weeks = _weeks_for_period(period_type, year, month)
    weekly_avg_income, weekly_avg_expense = _calculate_weekly_averages(
        total_income=total_income,
        total_expense=total_expense,
        weeks=weeks,
    )
    ratio = _calculate_income_expense_ratio(total_income, total_expense)

    _upsert_metrics(
        session,
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        transaction_count=tx_count,
        payment_method_breakdown=breakdown,
        weekly_average_income=weekly_avg_income,
        weekly_average_expense=weekly_avg_expense,
        income_expense_ratio=ratio,
    )
