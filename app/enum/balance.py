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


class PeriodType(StrEnum):
    """Enum for period types."""

    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TransactionSortBy(StrEnum):
    """Enum for transaction sort by."""

    DATE = "date"
    AMOUNT = "amount"
    REFERENCE = "reference"


class SortOrder(StrEnum):
    """Enum for sort order."""

    ASC = "asc"
    DESC = "desc"
