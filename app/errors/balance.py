from fastapi import HTTPException, status


class TransactionNotFoundException(HTTPException):
    """Exception raised when a transaction is not found."""

    def __init__(self, reference: str):
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
