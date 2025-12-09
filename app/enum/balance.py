from enum import StrEnum


class Type(StrEnum):
    """Enum for types."""

    DEBIT = "debit"
    CREDIT = "credit"


class PaymentMethod(StrEnum):
    """Enum for payment methods."""

    CASH = "cash"
    TRANSFER_PERSONAL_ACCOUNT = "personal_transfer"
    TRANSFER_PEGAZZO_ACCOUNT = "pegazzo_transfer"
