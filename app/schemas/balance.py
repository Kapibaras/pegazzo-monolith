from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.enum.balance import PaymentMethod, Type
from app.errors.transaction_metrics import InvalidMetricsPeriodException

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
