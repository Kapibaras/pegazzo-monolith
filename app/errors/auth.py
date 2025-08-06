from fastapi import HTTPException, status
from fastapi_jwt_auth.exceptions import AuthJWTException

from app.utils.logging_config import logger


class InvalidCredentials(HTTPException):
    """Invalid credentials error."""

    def __init__(self):
        """Initialize the exception with a detail message."""

        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


class InvalidRefreshToken(HTTPException):
    """Invalid refresh token error."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


class InvalidOrMissingToken(HTTPException):
    """Exception raised when the JWT token is invalid or missing."""

    def __init__(self, exc: AuthJWTException):
        """Initialize with the message from AuthJWTException."""
        logger.error("JWT error: %s", exc, exc_info=True)
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing authentication token")


class InvalidTokenException(HTTPException):
    """Exception raised when an invalid token is provided."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided.")


class ForbiddenRoleException(HTTPException):
    """Exception raised when a user is not authorized to access a resource."""

    def __init__(self, role: str, allowed_roles: list[str]):
        """Initialize the exception with a detail message."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden role provided. Role: {role}, Allowed roles: {allowed_roles}",
        )
