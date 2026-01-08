from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.enum.balance import PaymentMethod, Type

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
