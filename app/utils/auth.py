from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi_jwt_auth import AuthJWT


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
        try:
            return ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    @staticmethod
    def create_access_token(username: str, role: str, authorize: AuthJWT) -> tuple[str, str]:
        """Create and return a tuple (access_token, refresh_token)."""
        access_token = authorize.create_access_token(
            subject=username,
            user_claims={"role": role},
        )
        refresh_token = authorize.create_refresh_token(
            subject=username,
            user_claims={"role": role},
        )

        return access_token, refresh_token
