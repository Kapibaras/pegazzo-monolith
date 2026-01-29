from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.enum.balance import PaymentMethod, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    InvalidPaymentMethodException,
    InvalidTransactionTypeException,
    TransactionNotFoundException,
)
from app.errors.transaction_metrics import InvalidMetricsPeriodException
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    BalanceMetricsSimpleResponseSchema,
    ComparisonSchema,
    PaymentMethodBreakdownByTypeSchema,
    PaymentMethodBreakdownSchema,
    PeriodMetricsSchema,
    TransactionResponseSchema,
    TransactionSchema,
    WeeklyAveragesSchema,
)
from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change
from app.utils.metrics_defaults import zero_period_metrics, zero_response
from app.utils.periods import previous_period_key
from app.utils.reference import generate_reference


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
        if not metrics:
            return {
                "balance": 0,
                "total_income": 0,
                "total_expense": 0,
                "transaction_count": 0,
                "period": {"month": month, "year": year},
            }

        return {
            "balance": metrics.balance,
            "total_income": metrics.total_income,
            "total_expense": metrics.total_expense,
            "transaction_count": metrics.transaction_count,
            "period": {"month": month, "year": year},
        }

    def get_management_metrics(
        self,
        period: str,
        year: int | None = None,
        month: int | None = None,
        week: int | None = None,
    ) -> BalanceMetricsDetailedResponseSchema:
        """Get detailed balance metrics for dashboard using precomputed transaction_metrics."""

        period = (period or "").strip().lower()

        if period not in {"week", "month", "year"}:
            raise InvalidMetricsPeriodException

        if period == "week" and (week is None or month is None or year is None):
            raise InvalidMetricsPeriodException

        if period == "month" and (month is None or year is None):
            raise InvalidMetricsPeriodException

        if period == "year" and year is None:
            raise InvalidMetricsPeriodException

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
            return zero_response()

        def to_period_schema(row) -> PeriodMetricsSchema:
            if not row:
                return zero_period_metrics()
            return PeriodMetricsSchema(
                balance=float(row.balance or 0),
                total_income=float(row.total_income or 0),
                total_expense=float(row.total_expense or 0),
                transaction_count=int(row.transaction_count or 0),
            )

        current_schema = to_period_schema(current_row)
        previous_schema = to_period_schema(prev_row)

        # --- payment breakdown (OPTION B: credit + debit) ---
        breakdown: dict[str, Any] = {}
        if current_row and current_row.payment_method_breakdown:
            breakdown = dict(current_row.payment_method_breakdown)

        credit = breakdown.get("credit") or {}
        debit = breakdown.get("debit") or {}

        credit_amounts = credit.get("amounts") or {}
        credit_percentages = credit.get("percentages") or {}

        debit_amounts = debit.get("amounts") or {}
        debit_percentages = debit.get("percentages") or {}

        payment_breakdown_schema = PaymentMethodBreakdownByTypeSchema(
            credit=PaymentMethodBreakdownSchema(
                amounts=credit_amounts,
                percentages=credit_percentages,
            ),
            debit=PaymentMethodBreakdownSchema(
                amounts=debit_amounts,
                percentages=debit_percentages,
            ),
        )

        weekly_income = float(current_row.weekly_average_income) if current_row and current_row.weekly_average_income else 0.0
        weekly_expense = (
            float(current_row.weekly_average_expense) if current_row and current_row.weekly_average_expense else 0.0
        )
        ratio = float(current_row.income_expense_ratio) if current_row and current_row.income_expense_ratio else 0.0

        cur_balance = Decimal(str(current_schema.balance))
        prev_balance = Decimal(str(previous_schema.balance))
        cur_income = Decimal(str(current_schema.total_income))
        prev_income = Decimal(str(previous_schema.total_income))
        cur_expense = Decimal(str(current_schema.total_expense))
        prev_expense = Decimal(str(previous_schema.total_expense))

        comparison = ComparisonSchema(
            balance_change_percent=float(percent_change(cur_balance, prev_balance)),
            income_change_percent=float(percent_change(cur_income, prev_income)),
            expense_change_percent=float(percent_change(cur_expense, prev_expense)),
            transaction_change=int(current_schema.transaction_count - previous_schema.transaction_count),
        )

        return BalanceMetricsDetailedResponseSchema(
            current_period=current_schema,
            previous_period=previous_schema,
            comparison=comparison,
            payment_method_breakdown=payment_breakdown_schema,
            weekly_averages=WeeklyAveragesSchema(income=weekly_income, expense=weekly_expense),
            income_expense_ratio=ratio,
        )
