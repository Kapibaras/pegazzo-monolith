import math
from datetime import datetime, timezone
from types import SimpleNamespace

from app.enum.balance import PaymentMethod, PeriodType, SortOrder, TransactionSortBy, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    InvalidPaymentMethodException,
    InvalidTransactionTypeException,
    TransactionNotFoundException,
)
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    BalanceMetricsSimpleResponseSchema,
    BalanceTransactionsResponseSchema,
    BalanceTrendDataPointSchema,
    BalanceTrendResponseSchema,
    ComparisonSchema,
    PaginationSchema,
    TransactionResponseSchema,
    TransactionSchema,
    WeeklyAveragesSchema,
)
from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change_from_schemas, safe_float
from app.utils.periods import (
    current_period_key,
    payment_breakdown_schemas,
    period_bounds_utc,
    previous_period_key,
    to_period_schema,
    weekly_averages_and_ratio,
)
from app.utils.reference import generate_reference


def _build_historical_keys(current: PeriodKey, limit: int) -> list[PeriodKey]:
    """Return period keys ordered oldest -> newest."""
    keys: list[PeriodKey] = []
    cursor = current
    for _ in range(limit):
        keys.append(cursor)
        cursor = previous_period_key(cursor)
    keys.reverse()
    return keys


class BalanceService:
    """Balance service class."""

    def __init__(self, repository: BalanceRepository):
        """Initialize the balance service with a repository."""
        self.repository = repository

    def get_transaction(self, reference: str) -> TransactionResponseSchema:
        """Get a transaction by reference."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)
        return transaction

    def create_transaction(self, data: TransactionSchema) -> TransactionResponseSchema:
        """Create a new transaction."""

        if data.type not in Type:
            raise InvalidTransactionTypeException

        if data.payment_method not in PaymentMethod:
            raise InvalidPaymentMethodException

        if data.description and len(data.description) > 255:
            raise InvalidDescriptionLengthException

        transaction = Transaction(
            amount=data.amount,
            reference=generate_reference(data.type, data.payment_method),
            date=data.date if data.date else datetime.now(timezone.utc),
            type=data.type,
            description=data.description,
            payment_method=data.payment_method,
        )
        return self.repository.create_transaction(transaction)

    def delete_transaction(self, reference: str):
        """Delete a transaction."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)

        self.repository.delete_transaction(transaction)

    def update_transaction(self, reference: str, data: TransactionSchema) -> TransactionResponseSchema:
        """Update a transaction."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)

        if data.amount is not None:
            transaction.amount = data.amount

        if data.description is not None:
            if len(data.description) > 255:
                raise InvalidDescriptionLengthException
            transaction.description = data.description

        if data.payment_method is not None:
            if data.payment_method not in PaymentMethod:
                raise InvalidPaymentMethodException
            transaction.payment_method = data.payment_method

        return self.repository.update_transaction(transaction)

    def get_metrics(self, month: int | None = None, year: int | None = None) -> BalanceMetricsSimpleResponseSchema:
        """Get metrics."""
        if month is None and year is None:
            now = datetime.now(timezone.utc)
            month = now.month
            year = now.year

        metrics = self.repository.get_month_year_metrics(month=month, year=year)
        metrics = metrics or SimpleNamespace(
            balance=0,
            total_income=0,
            total_expense=0,
            transaction_count=0,
        )

        return {
            "balance": metrics.balance,
            "total_income": metrics.total_income,
            "total_expense": metrics.total_expense,
            "transaction_count": metrics.transaction_count,
            "period": {"month": month, "year": year},
        }

    def get_management_metrics(
        self,
        period: PeriodType,
        year: int | None = None,
        month: int | None = None,
        week: int | None = None,
    ) -> BalanceMetricsDetailedResponseSchema:
        """Get detailed balance metrics for dashboard using precomputed transaction_metrics."""

        current_key = PeriodKey(period_type=period, year=year, month=month, week=week)
        prev_key = previous_period_key(current_key)

        current_row = self.repository.get_period_metrics(
            period_type=current_key.period_type,
            year=current_key.year,
            month=current_key.month,
            week=current_key.week,
        )
        prev_row = self.repository.get_period_metrics(
            period_type=prev_key.period_type,
            year=prev_key.year,
            month=prev_key.month,
            week=prev_key.week,
        )

        if not current_row and not prev_row:
            return BalanceMetricsDetailedResponseSchema()

        current_schema = to_period_schema(current_row)
        previous_schema = to_period_schema(prev_row)

        payment_breakdown_schema = payment_breakdown_schemas(current_row)
        weekly_income, weekly_expense, ratio = weekly_averages_and_ratio(current_row)

        comparison = ComparisonSchema(
            balance_change_percent=percent_change_from_schemas(
                current_schema,
                previous_schema,
                "balance",
            ),
            income_change_percent=percent_change_from_schemas(
                current_schema,
                previous_schema,
                "total_income",
            ),
            expense_change_percent=percent_change_from_schemas(
                current_schema,
                previous_schema,
                "total_expense",
            ),
            transaction_change=(current_schema.transaction_count - previous_schema.transaction_count),
        )

        return BalanceMetricsDetailedResponseSchema(
            current_period=current_schema,
            previous_period=previous_schema,
            comparison=comparison,
            payment_method_breakdown=payment_breakdown_schema,
            weekly_averages=WeeklyAveragesSchema(income=weekly_income, expense=weekly_expense),
            income_expense_ratio=ratio,
        )

    def get_historical(self, period: PeriodType, limit: int) -> BalanceTrendResponseSchema:
        """Get historical trend from precomputed transaction_metrics."""
        now = datetime.now(timezone.utc)
        current_key = current_period_key(period_type=period, now=now)

        keys = _build_historical_keys(current_key, limit)

        rows = self.repository.get_metrics_for_keys(period_type=period.value, keys=keys)

        metrics_by_key = {
            (int(r.year), int(r.month) if r.month is not None else None, int(r.week) if r.week is not None else None): r
            for r in rows
        }

        data: list[BalanceTrendDataPointSchema] = []
        for key in keys:
            start_dt, end_dt = period_bounds_utc(key)
            row = metrics_by_key.get((key.year, key.month, key.week))

            data.append(
                BalanceTrendDataPointSchema(
                    period_start=start_dt,
                    period_end=end_dt,
                    total_income=safe_float(row, "total_income"),
                    total_expense=safe_float(row, "total_expense"),
                ),
            )

        return BalanceTrendResponseSchema(period_type=period, data=data)

    def get_transactions(
        self,
        period: PeriodType,
        year: int | None = None,
        month: int | None = None,
        week: int | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: TransactionSortBy = TransactionSortBy.DATE,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> BalanceTransactionsResponseSchema:
        """Get transactions for a given period with pagination & sorting."""

        key = PeriodKey(period_type=period, year=year, month=month, week=week)
        start_dt, end_dt = period_bounds_utc(key)

        offset = (page - 1) * limit

        total = self.repository.count_transactions_in_range(
            start_dt=start_dt,
            end_dt=end_dt,
        )

        rows = self.repository.list_transactions_in_range(
            start_dt=start_dt,
            end_dt=end_dt,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return BalanceTransactionsResponseSchema(
            transactions=rows,
            pagination=PaginationSchema(
                page=page,
                limit=limit,
                total=total,
                total_pages=(0 if total == 0 else math.ceil(total / limit)),
            ),
        )
