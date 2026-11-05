from fastapi import status

from app.errors import PegazzoException


class GarageNotFoundException(PegazzoException):
    """Exception raised when a garage is not found or does not belong to the driver."""

    def __init__(self, garage_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garage with id '{garage_id}' was not found",
        )
