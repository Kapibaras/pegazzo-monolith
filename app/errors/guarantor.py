from fastapi import status

from app.errors import PegazzoException


class GuarantorNotFoundException(PegazzoException):
    """Exception raised when a guarantor is not found."""

    def __init__(self, guarantor_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guarantor with id '{guarantor_id}' was not found",
        )


class GuarantorLimitReachedException(PegazzoException):
    """Exception raised when a driver already has the maximum number of guarantors."""

    def __init__(self, driver_id: str, limit: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Driver '{driver_id}' already has {limit} guarantors. Remove one before adding another",
        )


class GuarantorNotLinkedToDriverException(PegazzoException):
    """Exception raised when a guarantor is not linked to the specified driver."""

    def __init__(self, guarantor_id: int, driver_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guarantor '{guarantor_id}' is not linked to driver '{driver_id}'",
        )
