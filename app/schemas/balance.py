from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.enum.balance import PaymentMethod, PeriodType, SortOrder, TransactionSortBy, Type
from app.errors.transaction_metrics import InvalidMetricsPeriodException
from app.schemas.types import RequestUTCDatetime

DEFAULT_LIMITS: dict[PeriodType, int] = {
    PeriodType.WEEK: 8,
    PeriodType.MONTH: 6,
    PeriodType.YEAR: 3,
}

# * BODY SCHEMAS * #


class TransactionSchema(BaseModel):
    """Schema for creating a transaction."""

    amount: float = Field(..., description="Amount of the transaction")
    date: RequestUTCDatetime | None = Field(default=None, description="Date of the transaction")
    type: Type = Field(..., description="Type of the transaction")
    description: str = Field(..., description="Description of the transaction")
    payment_method: PaymentMethod = Field(..., description="Payment method of the transaction")


class TransactionPatchSchema(BaseModel):
    """Schema for updating a transaction."""

    amount: Optional[float] = None
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


class BalanceTransactionsQuerySchema(BaseModel):
    """Query params for GET /management/balance/transactions."""

    period: PeriodType = Field(..., description="One of: week, month, year")

    week: Optional[int] = Field(None, ge=1, le=53, description="Week number (1-53)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month number (1-12)")
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Year (e.g., 2026)")

    page: Annotated[int, Field(default=1, ge=1, description="Page number starting at 1")] = 1
    limit: Annotated[int, Field(default=10, ge=1, le=100, description="Records per page (max 100)")] = 10

    sort_by: TransactionSortBy = Field(
        default=TransactionSortBy.DATE,
        description="Column to sort by. One of: date, amount, reference",
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort direction. One of: asc, desc",
    )

    @model_validator(mode="after")
    def validate_period_requirements(self) -> "BalanceTransactionsQuerySchema":
        """Validate period requirements."""
        match self.period:
            case PeriodType.WEEK:
                if self.week is None or self.month is None or self.year is None:
                    raise InvalidMetricsPeriodException

            case PeriodType.MONTH:
                if self.month is None or self.year is None:
                    raise InvalidMetricsPeriodException
                if self.week is not None:
                    raise InvalidMetricsPeriodException

            case PeriodType.YEAR:
                if self.year is None:
                    raise InvalidMetricsPeriodException
                if self.month is not None or self.week is not None:
                    raise InvalidMetricsPeriodException

        return self


# * RESPONSE SCHEMAS * #


class TransactionResponseSchema(BaseModel):
    """Schema for transaction responses."""

    amount: float = Field(..., description="Amount of the transaction")
    reference: str = Field(..., description="Reference of the transaction")
    date: datetime = Field(..., description="Date of the transaction")
    type: Type = Field(..., description="Type of the transaction")
    description: str = Field(..., description="Description of the transaction")
    payment_method: PaymentMethod = Field(..., description="Payment method")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, v):
        """Normalize description to empty string if None."""
        return "" if v is None else v

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

    balance: float = Field(0.0, description="Balance for the period")
    total_income: float = Field(0.0, description="Total income for the period")
    total_expense: float = Field(0.0, description="Total expense for the period")
    transaction_count: int = Field(0, description="Number of transactions in the period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class ComparisonSchema(BaseModel):
    """Comparison between current and previous periods."""

    balance_change_percent: float = Field(0.0, description="Percent change in balance vs previous")
    income_change_percent: float = Field(0.0, description="Percent change in income vs previous")
    expense_change_percent: float = Field(0.0, description="Percent change in expense vs previous")
    transaction_change: int = Field(0, description="Absolute delta in transaction count vs previous")

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

    income: float = Field(0.0, description="Weekly average income for the period")
    expense: float = Field(0.0, description="Weekly average expense for the period")

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BalanceMetricsDetailedResponseSchema(BaseModel):
    """Response for the dashboard endpoint."""

    current_period: PeriodMetricsSchema = Field(default_factory=PeriodMetricsSchema)
    previous_period: PeriodMetricsSchema = Field(default_factory=PeriodMetricsSchema)
    comparison: ComparisonSchema = Field(default_factory=ComparisonSchema)
    payment_method_breakdown: PaymentMethodBreakdownByTypeSchema = Field(
        default_factory=PaymentMethodBreakdownByTypeSchema,
    )
    weekly_averages: WeeklyAveragesSchema = Field(default_factory=WeeklyAveragesSchema)
    income_expense_ratio: float = Field(0.0, description="Income/expense ratio for current period")

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


class PaginationSchema(BaseModel):
    """Pagination schema."""

    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class BalanceTransactionsResponseSchema(BaseModel):
    """Balance transactions response schema."""

    transactions: list[TransactionResponseSchema] = Field(default_factory=list)
    pagination: PaginationSchema = Field(...)

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
