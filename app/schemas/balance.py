from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.enum.balance import PaymentMethod, Type

# * BODY SCHEMAS * #


class TransactionSchema(BaseModel):
    """Schema for creating a transaction."""

    amount: int = Field(..., description="Amount of the transaction")
    date: datetime = Field(..., description="Date of the transaction")
    type: Type = Field(..., description="Type of the transaction")
    description: str = Field(..., description="Description of the transaction")
    payment_method: PaymentMethod = Field(..., description="Payment method of the transaction")


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


class PermissionsResponse(BaseModel):
    """Schema for permissions responses."""

    role: str = Field(..., description="Role of the user")
    permissions: list[str] = Field(..., description="Permissions of the user")


class ActionSuccess(BaseModel):
    """Schema for successful action responses (e.g., DELETE).

    Attributes:
        message (str): A descriptive message indicating the result of the action.
        extra_data (Any, optional): Additional data relevant to the action. Defaults to None.

    """

    message: str = Field(
        ...,
        description="Message indicating the action was successfully performed",
        example="User deleted successfully.",
    )
    extra_data: Optional[Any] = Field(default=None, description="Additional data relevant to the action")
