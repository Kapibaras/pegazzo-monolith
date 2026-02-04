from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.enum.balance import PaymentMethod, PeriodType, Type
from app.errors.transaction_metrics import InvalidMetricsPeriodException

DEFAULT_LIMITS: dict[PeriodType, int] = {
    PeriodType.WEEK: 8,
    PeriodType.MONTH: 6,
    PeriodType.YEAR: 3,
}

# * BODY SCHEMAS * #


class TransactionSchema(BaseModel):
    """Schema for creating a transaction."""

    amount: int = Field(..., description="Amount of the transaction")
    date: datetime | None = Field(default=None, description="Date of the transaction")
    type: Type = Field(..., description="Type of the transaction")
    description: str = Field(..., description="Description of the transaction")
    payment_method: PaymentMethod = Field(..., description="Payment method of the transaction")


class TransactionPatchSchema(BaseModel):
    """Schema for updating a transaction."""

    amount: Optional[int] = None
    description: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None


class BalanceMetricsQuerySchema(BaseModel):
    """Schema for balance metrics query."""

    month: int | None = Field(None, ge=1, le=12)
    year: int | None = Field(None, ge=2000)

    @model_validator(mode="after")
    def validate_month_year(self):
        """Validate month and year."""
        if (self.month is None) ^ (self.year is None):
            raise InvalidMetricsPeriodException
        return self


class BalanceMetricsDetailedQuerySchema(BaseModel):
    """Schema for balance metrics detailed query."""

    period: PeriodType = Field(..., description="One of: week, month, year")

    week: Optional[int] = Field(None, ge=1, le=53, description="ISO week number (1-53)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month number (1-12)")
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Year (e.g., 2026)")

    @model_validator(mode="after")
    def validate_period_requirements(self):
        """Validate period requirements."""
        if self.period == "week":
            if self.year is None or self.month is None or self.week is None:
                raise InvalidMetricsPeriodException
        elif self.period == "month":
            if self.year is None or self.month is None:
                raise InvalidMetricsPeriodException
            if self.week is not None:
                raise InvalidMetricsPeriodException
        elif self.period == "year":
            if self.year is None:
                raise InvalidMetricsPeriodException
            if self.month is not None or self.week is not None:
                raise InvalidMetricsPeriodException
        else:
            raise InvalidMetricsPeriodException

        return self


class BalanceTrendQuerySchema(BaseModel):
    """Schema for balance trend query params.

    - period: required, one of week/month/year
    - limit: optional; defaults depend on period; max 100
    """

    period: PeriodType = Field(
        ...,
        description="One of: week, month, year",
        examples=[PeriodType.MONTH],
    )

    limit: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=100,
            description=("Number of periods to return. Defaults: week=8, month=6, year=3. Max: 100."),
            examples=[6],
        ),
    ] = None

    @model_validator(mode="after")
    def apply_default_limit(self) -> "BalanceTrendQuerySchema":
        """Apply default limit based on period if not provided."""
        if self.limit is None:
            self.limit = DEFAULT_LIMITS[self.period]
        return self


# * RESPONSE SCHEMAS * #


class TransactionResponseSchema(BaseModel):
    """Schema for transaction responses."""

    amount: int = Field(..., description="Amount of the transaction")
    reference: str = Field(..., description="Reference of the transaction")
    date: datetime = Field(..., description="Date of the transaction")
    type: Type = Field(..., description="Type of the transaction")
    description: str = Field(..., description="Description of the transaction")
    payment_method: PaymentMethod = Field(..., description="Payment method")

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BalancePeriodSchema(BaseModel):
    """Schema for balance period."""

    month: int = Field(..., ge=1, le=12, description="Month of the period")
    year: int = Field(..., ge=2000, description="Year of the period")


class BalanceMetricsSimpleResponseSchema(BaseModel):
    """Schema for balance metrics."""

    balance: float = Field(..., description="Balance")
    total_income: float = Field(..., description="Total income")
    total_expense: float = Field(..., description="Total expense")
    transaction_count: int = Field(..., description="Transaction count")
    period: BalancePeriodSchema = Field(..., description="Period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class PeriodMetricsSchema(BaseModel):
    """Metrics for a period (current or previous)."""

    balance: float = Field(..., description="Balance for the period")
    total_income: float = Field(..., description="Total income for the period")
    total_expense: float = Field(..., description="Total expense for the period")
    transaction_count: int = Field(..., description="Number of transactions in the period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class ComparisonSchema(BaseModel):
    """Comparison between current and previous periods."""

    balance_change_percent: float = Field(..., description="Percent change in balance vs previous")
    income_change_percent: float = Field(..., description="Percent change in income vs previous")
    expense_change_percent: float = Field(..., description="Percent change in expense vs previous")
    transaction_change: int = Field(..., description="Absolute delta in transaction count vs previous")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class PaymentMethodBreakdownSchema(BaseModel):
    """Payment method breakdown from JSONB."""

    amounts: dict[str, float] = Field(default_factory=dict, description="Amounts by payment method")
    percentages: dict[str, float] = Field(default_factory=dict, description="Percentages by payment method")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class PaymentMethodBreakdownByTypeSchema(BaseModel):
    """Payment method breakdown by transaction type."""

    credit: PaymentMethodBreakdownSchema = Field(default_factory=PaymentMethodBreakdownSchema)
    debit: PaymentMethodBreakdownSchema = Field(default_factory=PaymentMethodBreakdownSchema)

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class WeeklyAveragesSchema(BaseModel):
    """Weekly averages for the current period."""

    income: float = Field(..., description="Weekly average income for the period")
    expense: float = Field(..., description="Weekly average expense for the period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BalanceMetricsDetailedResponseSchema(BaseModel):
    """Response for the dashboard endpoint."""

    current_period: PeriodMetricsSchema = Field(..., description="Metrics for the requested period")
    previous_period: PeriodMetricsSchema = Field(..., description="Metrics for the previous period")
    comparison: ComparisonSchema = Field(..., description="Comparison between current and previous")
    payment_method_breakdown: PaymentMethodBreakdownByTypeSchema = Field(
        default_factory=PaymentMethodBreakdownByTypeSchema,
        description="Payment method breakdown separated by transaction type (credit/debit)",
    )
    weekly_averages: WeeklyAveragesSchema = Field(..., description="Weekly averages for current period")
    income_expense_ratio: float = Field(..., description="Income/expense ratio for current period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BalanceTrendDataPointSchema(BaseModel):
    """A single historical data point for the requested period."""

    period_start: datetime = Field(
        ...,
        description="Start datetime of the period (ISO 8601).",
        examples=[datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc)],
    )
    period_end: datetime = Field(
        ...,
        description="End datetime of the period (ISO 8601).",
        examples=[datetime(2025, 8, 31, 23, 59, 59, tzinfo=timezone.utc)],
    )
    total_income: float = Field(
        ...,
        description="Total income for this period.",
        examples=[4000.00],
    )
    total_expense: float = Field(
        ...,
        description="Total expense for this period.",
        examples=[2000.00],
    )

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BalanceTrendResponseSchema(BaseModel):
    """Historical trend response for balance metrics."""

    period_type: PeriodType = Field(
        ...,
        description="The type of period requested (week, month, year).",
        examples=[PeriodType.MONTH],
    )
    data: list[BalanceTrendDataPointSchema] = Field(
        ...,
        description=(
            "Array of period data points ordered chronologically (oldest to newest). "
            "Missing periods within the requested range must be included with totals set to 0."
        ),
    )

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )
