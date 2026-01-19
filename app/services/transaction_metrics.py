from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.enum.balance import Type as TxType
from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics

DEC_2 = Decimal("0.01")


@dataclass(frozen=True)
class PeriodKey:
    """Identifies a metrics period."""

    period_type: str
    year: int
    month: Optional[int] = None
    week: Optional[int] = None


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _start_of_month(year: int, month: int) -> date:
    """Return first day of month."""
    return date(year, month, 1)


def _end_of_month(year: int, month: int) -> date:
    """Return last day of month."""
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _start_of_year(year: int) -> date:
    """Return first day of year."""
    return date(year, 1, 1)


def _end_of_year(year: int) -> date:
    """Return last day of year."""
    return date(year, 12, 31)


def _weeks_in_month(year: int, month: int) -> int:
    """Count distinct ISO weeks overlapping a month."""
    start = _start_of_month(year, month)
    end = _end_of_month(year, month)
    weeks: set[tuple[int, int]] = set()
    cur = start
    while cur <= end:
        iso = cur.isocalendar()
        weeks.add((iso.year, iso.week))
        cur += timedelta(days=1)
    return max(1, len(weeks))


def _weeks_in_year(year: int) -> int:
    """ISO weeks in a year (Dec 28 is always in the last ISO week)."""
    return date(year, 12, 28).isocalendar().week


def _decimal_2(value: Any) -> Decimal:
    """Convert to Decimal(2) safely."""
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(DEC_2, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(DEC_2, rounding=ROUND_HALF_UP)


def _pct(value: Decimal, total: Decimal) -> Decimal:
    """Return a percentage with 2 decimals."""
    if total == 0:
        return Decimal("0.00")
    return (value * Decimal("100") / total).quantize(DEC_2, rounding=ROUND_HALF_UP)


def _build_breakdown(amounts: dict[str, Decimal]) -> dict[str, Any]:
    """Build JSON breakdown {amounts, percentages}."""
    total = sum(amounts.values(), Decimal("0.00"))
    return {
        "amounts": {k: float(v) for k, v in amounts.items()},
        "percentages": {k: float(_pct(v, total)) for k, v in amounts.items()},
    }


def _periods_for_datetime(dt: datetime) -> list[PeriodKey]:
    """Return affected week/month/year period keys for a datetime."""
    dt = _ensure_utc(dt)
    d = dt.date()

    iso = d.isocalendar()
    iso_year = iso.year
    iso_week = iso.week

    return [
        PeriodKey(period_type="week", year=iso_year, month=None, week=iso_week),
        PeriodKey(period_type="month", year=d.year, month=d.month),
        PeriodKey(period_type="year", year=d.year),
    ]


def _period_date_range(key: PeriodKey) -> tuple[date, date]:
    """Return inclusive [start, end] dates for a given period key."""
    if key.period_type == "week":
        if key.week is None:
            raise TransactionMetricsPeriodError.week_requires_week()
        start = date.fromisocalendar(key.year, key.week, 1)
        end = start + timedelta(days=6)
        return start, end

    if key.period_type == "month":
        if key.month is None:
            raise TransactionMetricsPeriodError.month_requires_month()
        return _start_of_month(key.year, key.month), _end_of_month(key.year, key.month)

    if key.period_type == "year":
        return _start_of_year(key.year), _end_of_year(key.year)

    raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)


def recalc_period_metrics(
    session: Session,
    *,
    period_type: str,
    year: int,
    month: int | None,
    week: int | None,
) -> None:
    """Recalculate metrics for a single period and UPSERT the row."""
    key = PeriodKey(period_type=period_type, year=year, month=month, week=week)
    start_d, end_d = _period_date_range(key)

    start_dt = datetime.combine(start_d, datetime.min.time(), tzinfo=timezone.utc)
    end_dt_exclusive = datetime.combine(end_d + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    base_filter = (Transaction.date >= start_dt) & (Transaction.date < end_dt_exclusive)

    totals_stmt = select(
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

    totals = session.execute(totals_stmt).one()
    total_income = _decimal_2(totals.total_income)
    total_expense = _decimal_2(totals.total_expense)
    tx_count = int(totals.tx_count or 0)

    balance = (total_income - total_expense).quantize(DEC_2, rounding=ROUND_HALF_UP)

    breakdown_stmt = (
        select(
            Transaction.payment_method.label("payment_method"),
            func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
        )
        .where(base_filter)
        .group_by(Transaction.payment_method)
    )
    rows = session.execute(breakdown_stmt).all()
    amounts: dict[str, Decimal] = {str(r.payment_method): _decimal_2(r.amount) for r in rows}
    payment_method_breakdown = _build_breakdown(amounts)

    if period_type == "week":
        weeks = 1
    elif period_type == "month":
        weeks = _weeks_in_month(year, month or 1)
    else:
        weeks = _weeks_in_year(year)

    weekly_average_income = (total_income / Decimal(weeks)).quantize(DEC_2, rounding=ROUND_HALF_UP)
    weekly_average_expense = (total_expense / Decimal(weeks)).quantize(DEC_2, rounding=ROUND_HALF_UP)

    if total_expense == 0:
        ratio = Decimal("0.00")
    else:
        ratio = (total_income / total_expense).quantize(DEC_2, rounding=ROUND_HALF_UP)

    stmt = insert(TransactionMetrics).values(
        period_type=period_type,
        year=year,
        month=month,
        week=week,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        transaction_count=tx_count,
        payment_method_breakdown=payment_method_breakdown,
        weekly_average_income=weekly_average_income,
        weekly_average_expense=weekly_average_expense,
        income_expense_ratio=ratio,
        updated_at=func.now(),
    )

    if period_type == "week":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year", "week"],
            index_where=(TransactionMetrics.period_type == "week"),
            set_={
                "total_income": stmt.excluded.total_income,
                "total_expense": stmt.excluded.total_expense,
                "balance": stmt.excluded.balance,
                "transaction_count": stmt.excluded.transaction_count,
                "payment_method_breakdown": stmt.excluded.payment_method_breakdown,
                "weekly_average_income": stmt.excluded.weekly_average_income,
                "weekly_average_expense": stmt.excluded.weekly_average_expense,
                "income_expense_ratio": stmt.excluded.income_expense_ratio,
                "updated_at": func.now(),
            },
        )
    elif period_type == "month":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year", "month"],
            index_where=(TransactionMetrics.period_type == "month"),
            set_={
                "total_income": stmt.excluded.total_income,
                "total_expense": stmt.excluded.total_expense,
                "balance": stmt.excluded.balance,
                "transaction_count": stmt.excluded.transaction_count,
                "payment_method_breakdown": stmt.excluded.payment_method_breakdown,
                "weekly_average_income": stmt.excluded.weekly_average_income,
                "weekly_average_expense": stmt.excluded.weekly_average_expense,
                "income_expense_ratio": stmt.excluded.income_expense_ratio,
                "updated_at": func.now(),
            },
        )
    elif period_type == "year":
        stmt = stmt.on_conflict_do_update(
            index_elements=["year"],
            index_where=(TransactionMetrics.period_type == "year"),
            set_={
                "total_income": stmt.excluded.total_income,
                "total_expense": stmt.excluded.total_expense,
                "balance": stmt.excluded.balance,
                "transaction_count": stmt.excluded.transaction_count,
                "payment_method_breakdown": stmt.excluded.payment_method_breakdown,
                "weekly_average_income": stmt.excluded.weekly_average_income,
                "weekly_average_expense": stmt.excluded.weekly_average_expense,
                "income_expense_ratio": stmt.excluded.income_expense_ratio,
                "updated_at": func.now(),
            },
        )
    else:
        raise TransactionMetricsPeriodError.unknown_period_type(period_type)

    session.execute(stmt)


def update_metrics_for_transaction(
    session: Session,
    *,
    transaction: Transaction,
    old_transaction: Transaction | None = None,
) -> None:
    """Update all period metrics affected by a transaction insert/update/delete."""
    new_periods = set(_periods_for_datetime(transaction.date))
    affected = set(new_periods)

    if old_transaction is not None:
        affected |= set(_periods_for_datetime(old_transaction.date))

    for key in affected:
        recalc_period_metrics(
            session,
            period_type=key.period_type,
            year=key.year,
            month=key.month,
            week=key.week,
        )
