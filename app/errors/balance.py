from fastapi import HTTPException, status


class TransactionNotFoundException(HTTPException):
    """Exception raised when a transaction is not found."""

    def __init__(self, reference: str):
        """Transaction that was not found."""

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with reference '{reference}' was not found",
        )


class InvalidDescriptionLengthException(HTTPException):
    """Description length is invalid."""

    def __init__(self):
        """Exception raised when description exceeds 255 characters."""

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be 255 characters or fewer",
        )


class InvalidTransactionTypeException(HTTPException):
    """Invalid transaction type error."""

    def __init__(self):
        """Exception raised when transaction type is invalid."""

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction type",
        )


class InvalidPaymentMethodException(HTTPException):
    """Invalid payment method error."""

    def __init__(self):
        """Exception raised when payment method is invalid."""

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment method",
        )


class TransactionStatusForbiddenException(HTTPException):
    """403 - Admin tried to set a status other than PENDING."""

    def __init__(self):
        """Exception raised when admin sets a status other than PENDING."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only set transaction status to PENDING",
        )


class InvalidTransactionStatusTransitionException(HTTPException):
    """422 - Admin tried to authorize a non-REJECTED transaction."""

    def __init__(self):
        """Exception raised when admin tries to resubmit a non-REJECTED transaction."""
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Admins can only re-submit REJECTED transactions to PENDING",
        )


class TransactionEditForbiddenException(HTTPException):
    """403 - Admin tried to edit a non-REJECTED transaction."""

    def __init__(self):
        """Exception raised when admin tries to edit a non-REJECTED transaction."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only edit REJECTED transactions",
        )


class TransactionDeleteForbiddenException(HTTPException):
    """403 - Admin tried to delete a non-REJECTED transaction."""

    def __init__(self):
        """Exception raised when admin tries to delete a non-REJECTED transaction."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins can only delete REJECTED transactions",
        )
