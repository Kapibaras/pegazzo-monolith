from fastapi import status

from app.errors import PegazzoException


class InsuranceNotFoundException(PegazzoException):
    """Exception raised when an insurance provider is not found."""

    def __init__(self, insurance_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance provider with id '{insurance_id}' was not found",
        )


class InsuranceNameAlreadyExistsException(PegazzoException):
    """Exception raised when an insurance provider name already exists."""

    def __init__(self, name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An insurance provider with name '{name}' already exists",
        )


class InsuranceInUseException(PegazzoException):
    """Exception raised when trying to delete an insurance provider that is referenced by a car."""

    def __init__(self, insurance_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insurance provider '{insurance_id}' cannot be deleted because it is referenced by one or more cars",
        )
