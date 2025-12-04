from enum import StrEnum


class Type(StrEnum):
    """Enum for types."""

    DEBIT = "cargo"
    CREDIT = "abono"


class PaymentMethod(StrEnum):
    """Enum for payment methods."""

    CASH = "efectivo"
    TRANSFER_PERSONAL_ACCOUNT = "transferencia personal"
    TRANSFER_PEGAZZO_ACCOUNT = "transferencia pegazzo"
