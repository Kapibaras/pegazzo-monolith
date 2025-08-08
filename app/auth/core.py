from datetime import timedelta

from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel

from app.config import AUTHORIZATION, ENVIRONMENT


class Settings(BaseModel):
    """Settings for the AuthJWT library."""

    authjwt_secret_key: str = AUTHORIZATION.JWT_SECRET_KEY
    authjwt_token_location: set[str] = {"cookies"}
    authjwt_cookie_csrf_protect: bool = ENVIRONMENT != "LOCAL"
    authjwt_cookie_secure: bool = True
    authjwt_cookie_samesite: str = "lax"
    authjwt_cookie_httponly: bool = True
    authjwt_access_token_expires: timedelta = timedelta(minutes=(AUTHORIZATION.JWT_ACCESS_TOKEN_EXPIRES_MIN))
    authjwt_refresh_token_expires: timedelta = timedelta(days=(AUTHORIZATION.JWT_REFRESH_TOKEN_EXPIRES_DAYS))
    authjwt_access_cookie_key: str = "access_token_cookie"
    authjwt_refresh_cookie_key: str = "refresh_token_cookie"


@AuthJWT.load_config
def get_config():
    """Get the configuration for the AuthJWT library."""
    return Settings()
