from fastapi import status

from app.errors import PegazzoException


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
