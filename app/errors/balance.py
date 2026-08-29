from fastapi import status

from app.errors import PegazzoException


class TransactionNotFoundException(PegazzoException):
    """Exception raised when a transaction is not found."""

    def __init__(self, reference: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with reference '{reference}' was not found",
        )


class InvalidDescriptionLengthException(PegazzoException):
    """Description length is invalid."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be 255 characters or fewer",
        )


class InvalidTransactionTypeException(PegazzoException):
    """Invalid transaction type error."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction type",
        )


class InvalidPaymentMethodException(PegazzoException):
    """Invalid payment method error."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment method",
        )


class TransactionStatusForbiddenException(PegazzoException):
    """403 - Admin tried to set a status other than PENDING."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only set transaction status to PENDING",
        )


class InvalidTransactionStatusTransitionException(PegazzoException):
    """422 - Admin tried to authorize a non-REJECTED transaction."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Admins can only re-submit REJECTED transactions to PENDING",
        )


class TransactionEditForbiddenException(PegazzoException):
    """403 - Admin tried to edit a non-REJECTED transaction."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only edit REJECTED transactions",
        )


class TransactionDeleteForbiddenException(PegazzoException):
    """403 - Admin tried to delete a non-REJECTED transaction."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only delete REJECTED transactions",
        )
