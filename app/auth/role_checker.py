from typing import List, Optional, Tuple

from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

from app.errors.auth import ForbiddenRoleException, InvalidOrMissingToken, InvalidTokenException


class RoleChecker:
    """Role checker class."""

    def __init__(self, allowed_roles: Optional[List[str]] = []) -> None:
        """Initialize the role checker."""
        self.allowed_roles = allowed_roles

    def __call__(self, authorize: AuthJWT = Depends()) -> Tuple[str, str]:
        """Check if the role is allowed."""
        try:
            authorize.jwt_required()
        except AuthJWTException as e:
            raise InvalidOrMissingToken from e

        claims = authorize.get_raw_jwt()
        username = claims.get("sub")
        role = claims.get("role")

        if not username or not role:
            raise InvalidTokenException

        if not self.allowed_roles:
            raise ForbiddenRoleException(role, [])

        if role not in self.allowed_roles:
            raise ForbiddenRoleException(role, self.allowed_roles)

        return username, role
