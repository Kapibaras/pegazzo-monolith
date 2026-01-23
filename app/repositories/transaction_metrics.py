from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.enum.balance import Type as TxType
from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.schemas.dto.periods import PeriodKey, PeriodRawMetrics
from app.utils.decimal import DEC_2, round_to_2_decimals
from app.utils.metrics import calculate_income_expense_ratio, calculate_weekly_averages
from app.utils.paymenth_method import format_payment_method_breakdown
from app.utils.periods import get_period_date_range, weeks_for_period

from .abstract import DBRepository

logger = logging.getLogger(__name__)


class TransactionMetricsRepository(DBRepository):
    """Repository for transaction metrics aggregation and persistence."""

    def recalc_period(
        self,
        period_type: str,
        year: int,
        month: int | None = None,
        week: int | None = None,
        commit: bool = True,
    ) -> None:
        """Recalculate metrics for a single period and UPSERT the row."""

        key = PeriodKey(
            period_type=period_type,
            year=year,
            month=month,
            week=week,
        )

        start_d, end_d = get_period_date_range(key)

        base_filter = (
            Transaction.date >= start_d,
            Transaction.date < end_d,
        )

        metrics = self._fetch_period_metrics(base_filter)

        balance = (metrics.total_income - metrics.total_expense).quantize(
            DEC_2,
            rounding=ROUND_HALF_UP,
        )

        breakdown = format_payment_method_breakdown(metrics.payment_amounts)

        weeks = weeks_for_period(period_type, year, month)

        weekly_avg_income, weekly_avg_expense = calculate_weekly_averages(
            total_income=metrics.total_income,
            total_expense=metrics.total_expense,
            weeks=weeks,
        )

        ratio = calculate_income_expense_ratio(
            metrics.total_income,
            metrics.total_expense,
        )

        self._upsert_metrics(
            period_type=period_type,
            year=year,
            month=month,
            week=week,
            total_income=metrics.total_income,
            total_expense=metrics.total_expense,
            balance=balance,
            transaction_count=metrics.transaction_count,
            payment_method_breakdown=breakdown,
            weekly_average_income=weekly_avg_income,
            weekly_average_expense=weekly_avg_expense,
            income_expense_ratio=ratio,
            commit=commit,
        )

    def _fetch_period_metrics(self, base_filter: Iterable[Any]) -> PeriodRawMetrics:
        stmt = (
            select(
                Transaction.type,
                Transaction.payment_method,
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                func.count().label("tx_count"),
            )
            .where(*base_filter)
            .group_by(Transaction.type, Transaction.payment_method)
        )

        try:
            rows = self.db.execute(stmt).all()
        except Exception:
            logger.exception("Failed fetching transaction metrics")
            raise

        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        transaction_count = 0
        payment_amounts: dict[str, Decimal] = {}

        for r in rows:
            amount = round_to_2_decimals(r.amount)
            transaction_count += int(r.tx_count or 0)

            if r.type == TxType.CREDIT.value:
                total_income += amount
            elif r.type == TxType.DEBIT.value:
                total_expense += amount

            key = str(r.payment_method)
            payment_amounts[key] = payment_amounts.get(key, Decimal("0.00")) + amount

        return PeriodRawMetrics(
            total_income=round_to_2_decimals(total_income),
            total_expense=round_to_2_decimals(total_expense),
            transaction_count=transaction_count,
            payment_amounts=payment_amounts,
        )

    def _upsert_metrics(
        self,
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
        commit: bool = True,
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
            self.db.execute(stmt)
            if commit:
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    logger.exception(...)
                raise
        except Exception:
            self.db.rollback()
            logger.exception(
                "Failed upserting metrics for period=%s y=%s m=%s w=%s",
                period_type,
                year,
                month,
                week,
            )
            raise
