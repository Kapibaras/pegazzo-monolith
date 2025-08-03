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
