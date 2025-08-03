from datetime import timedelta

from argon2 import PasswordHasher
from fastapi_jwt_auth import AuthJWT

from app.config import JWT_ACCESS_TOKEN_EXPIRES_MIN, JWT_REFRESH_TOKEN_EXPIRES_DAYS


class AuthUtils:
    """Utils for authentication."""

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a password."""
        ph = PasswordHasher()
        return ph.hash(plain_password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        ph = PasswordHasher()
        return ph.verify(hashed_password, plain_password)

    @staticmethod
    def create_access_token(username: str, role: str, authorize: AuthJWT) -> tuple[str, str]:
        """Crea y devuelve una tupla (access_token, refresh_token)."""
        access_token_expires = timedelta(minutes=int(JWT_ACCESS_TOKEN_EXPIRES_MIN))
        refresh_token_expires = timedelta(days=int(JWT_REFRESH_TOKEN_EXPIRES_DAYS))

        access_token = authorize.create_access_token(
            subject=username,
            user_claims={"role": role},
            expires_time=access_token_expires,
        )
        refresh_token = authorize.create_refresh_token(
            subject=username,
            user_claims={"role": role},
            expires_time=refresh_token_expires,
        )

        return access_token, refresh_token
