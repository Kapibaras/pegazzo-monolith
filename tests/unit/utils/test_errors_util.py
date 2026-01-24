class MissingDatabaseURLError(RuntimeError):
    """Raised when DATABASE_URL env var is missing for metrics tests."""

    def __init__(self) -> None:
        """Initialize the exception. Raises: RuntimeError: If DATABASE_URL env var is missing."""
        super().__init__("DATABASE_URL env var is required for metrics_db_session tests")


class DatabaseError(Exception):
    """Raised when there is a database error."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__("DATABASE_URL env var is required for metrics_db_session tests")
