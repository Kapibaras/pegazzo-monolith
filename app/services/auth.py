from fastapi_jwt_auth import AuthJWT

from app.errors.auth import InvalidCredentials, InvalidRefreshToken
from app.errors.user import UserNotFoundException
from app.repositories.user import UserRepository
from app.utils.auth import AuthUtils


class AuthService:
    """Authentication service."""

    def __init__(self, authorize: AuthJWT, repository: UserRepository):
        """Initialize the service with an authorize instance."""

        self.authorize = authorize
        self.repository = repository

    def login(self, username: str, password_attempt: str) -> str:
        """Login a user and return an action success response."""

        user = self.repository.get_by_username(username)
        if not user:
            raise UserNotFoundException

        if not AuthUtils.verify_password(password_attempt, user.password):
            raise InvalidCredentials

        access_token, refresh_token = AuthUtils.create_access_token(
            username=user.username,
            role=user.role.name,
            authorize=self.authorize,
        )
        self.authorize.set_access_cookies(access_token)
        self.authorize.set_refresh_cookies(refresh_token)

    def refresh(self) -> str:
        """Refresh a user's access token and return an action success response."""

        try:
            self.authorize.jwt_refresh_token_required()
        except Exception as ex:
            raise InvalidRefreshToken from ex

        current_user = self.authorize.get_jwt_subject()
        claims = self.authorize.get_raw_jwt()

        access_token, refresh_token = AuthUtils.create_access_token(
            username=current_user,
            role=claims.get("role"),
            authorize=self.authorize,
        )

        self.authorize.set_access_cookies(access_token)
        self.authorize.set_refresh_cookies(refresh_token)

    def logout(self) -> str:
        """Logout a user and return an action success response."""

        self.authorize.unset_jwt_cookies()
