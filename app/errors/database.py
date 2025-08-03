from fastapi import HTTPException, status


class DBOperationError(HTTPException):
    """Database operation error."""

    def __init__(self, detail: str = "Database operation failed"):
        """Initialize the exception with a detail message."""

        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
