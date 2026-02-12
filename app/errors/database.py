from typing import ClassVar

from fastapi import HTTPException, status


class DBOperationError(HTTPException):
    """Database operation error."""

    MESSAGES: ClassVar[dict[str, str]] = {
        "update": "Error updating transaction in the database",
        "create": "Error creating record in the database",
        "delete": "Error deleting record from the database",
        "fetch": "Error fetching record from the database",
        "default": "Database operation failed",
    }

    def __init__(self, operation: str = "default"):
        """Initialize the exception with a detail message.

        Args:
            operation: The operation that failed (update, create, delete, fetch, default)

        """
        detail = self.MESSAGES.get(operation, self.MESSAGES["default"])
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
