from fastapi import HTTPException, status
from fastapi_jwt_auth.exceptions import AuthJWTException


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
        msg = getattr(exc, "message", None) or getattr(exc, "detail", None) or repr(exc)
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)


class InvalidTokenException(HTTPException):
    """Exception raised when an invalid token is provided."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided.")


class ForbiddenRoleException(HTTPException):
    """Exception raised when a user is not authorized to access a resource."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role provided.")
