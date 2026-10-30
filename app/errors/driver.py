from fastapi import status

from app.errors import PegazzoException


class DriverNotFoundException(PegazzoException):
    """Exception raised when a driver is not found."""

    def __init__(self, driver_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id '{driver_id}' was not found",
        )


class DriverHasActiveContractException(PegazzoException):
    """Exception raised when trying to archive a driver with an active contract."""

    def __init__(self, driver_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot archive driver '{driver_id}' because they have an active contract",
        )


class DriverNotArchivedException(PegazzoException):
    """Exception raised when trying to delete a driver that is not archived."""

    def __init__(self, driver_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver '{driver_id}' must be archived before deletion",
        )


class DriverIdAlreadyExistsException(PegazzoException):
    """Exception raised when a driver id already exists."""

    def __init__(self, driver_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver with id '{driver_id}' already exists",
        )


class IdentificationNumberAlreadyExistsException(PegazzoException):
    """Exception raised when an identification number already exists."""

    def __init__(self, identification_number: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identification number '{identification_number}' already exists",
        )


class LicenseNumberAlreadyExistsException(PegazzoException):
    """Exception raised when a license number already exists."""

    def __init__(self, license_number: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"License number '{license_number}' already exists",
        )


class LicenseValidityInPastException(PegazzoException):
    """Exception raised when the license validity date is in the past."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License validity cannot be a past date",
        )
