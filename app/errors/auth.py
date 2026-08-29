from fastapi import status

from app.errors import PegazzoException


class InvalidCredentials(PegazzoException):
    """Invalid credentials error."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


class InvalidRefreshToken(PegazzoException):
    """Invalid refresh token error."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


class InvalidOrMissingToken(PegazzoException):
    """Exception raised when the JWT token is invalid or missing."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or missing authentication")


class InvalidTokenException(PegazzoException):
    """Exception raised when an invalid token is provided."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token provided")


class ForbiddenRoleException(PegazzoException):
    """Exception raised when a user is not authorized to access a resource."""

    def __init__(self, role: str, allowed_roles: list[str]):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden role provided. Role: {role}, Allowed roles: {allowed_roles}",
        )


class AlreadyLoggedOutException(PegazzoException):
    """Exception raised when a user tries to log out but is already logged out."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="No active session found to log out")
