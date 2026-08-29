from fastapi import status

from app.errors import PegazzoException


class DBOperationError(PegazzoException):
    """Generic database operation error."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
