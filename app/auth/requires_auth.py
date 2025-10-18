from dataclasses import dataclass
from typing import List, Optional

from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

from app.errors.auth import ForbiddenRoleException, InvalidOrMissingToken, InvalidTokenException


@dataclass(frozen=True)
class AuthUser:
    """AuthUser represents the authenticated user information."""

    username: str
    role: str


class RequiresAuth:
    """RequiresAuth is a dependency that checks for authentication and authorization."""

    def __init__(self, whitelist_roles: Optional[str | List[str]] = None) -> None:
        """Analyze if it has authentication and valid authorization.

        Args:
            whitelist_roles (Optional[List[str]]): List of roles allowed to access the resource. If empty, all roles are allowed.

        """
        self.whitelist_roles: List[str] = whitelist_roles if whitelist_roles else []

    def __call__(self, authorize: AuthJWT = Depends()) -> AuthUser:
        """Validate the JWT token and check the role."""
        try:
            authorize.jwt_required()
        except AuthJWTException as e:
            raise InvalidOrMissingToken from e

        claims = authorize.get_raw_jwt()
        username = claims.get("sub")
        role = claims.get("role")

        if not username or not role:
            raise InvalidTokenException

        if self.whitelist_roles and role not in self.whitelist_roles:
            raise ForbiddenRoleException(role, self.whitelist_roles)

        return AuthUser(username=username, role=role)
