from fastapi import HTTPException, status


class UsernameAlreadyExistsException(HTTPException):
    """Exception raised when a username already exists."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")


class InvalidRoleException(HTTPException):
    """Exception raised when an invalid role is provided."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role provided")


class InvalidPasswordException(HTTPException):
    """Exception raised when invalid credentials are provided."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


class UserNotFoundException(HTTPException):
    """Exception raised when a user is not found."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


class RoleNotFoundException(HTTPException):
    """Exception raised when a role is not found."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")


class ForbiddenRoleException(HTTPException):
    """Exception raised when a forbidden role is provided."""

    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role provided")
