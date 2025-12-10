from fastapi import HTTPException, status


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

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or missing authentication")


class InvalidTokenException(HTTPException):
    """Exception raised when an invalid token is provided."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided")


class ForbiddenRoleException(HTTPException):
    """Exception raised when a user is not authorized to access a resource."""

    def __init__(self, role: str, allowed_roles: list[str]):
        """Initialize the exception with a detail message."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden role provided. Role: {role}, Allowed roles: {allowed_roles}",
        )


class AlreadyLoggedOutException(HTTPException):
    """Exception raised when a user tries to log out but is already logged out."""

    def __init__(self):
        """Initialize the exception with a detail message."""
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="No active session found to log out")
