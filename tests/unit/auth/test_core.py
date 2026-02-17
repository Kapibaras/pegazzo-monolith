from datetime import timedelta

from app.auth.core import Settings
from app.config import AUTHORIZATION


class TestAuthJWTSettings:
    """Class of tests for AuthJWT configuration."""

    def test_settings_instance(self):
        settings = Settings()
        assert isinstance(settings, Settings)

    def test_settings_values(self):
        settings = Settings()
        assert settings.authjwt_secret_key == AUTHORIZATION.JWT_SECRET_KEY
        assert settings.authjwt_token_location == {"cookies"}
        assert settings.authjwt_cookie_csrf_protect is True
        assert settings.authjwt_cookie_secure is True
        assert settings.authjwt_cookie_samesite == "lax"
        assert settings.authjwt_cookie_httponly is True
        assert settings.authjwt_access_token_expires == timedelta(minutes=int(AUTHORIZATION.JWT_ACCESS_TOKEN_EXPIRES_MIN))
        assert settings.authjwt_refresh_token_expires == timedelta(days=int(AUTHORIZATION.JWT_REFRESH_TOKEN_EXPIRES_DAYS))
        assert settings.authjwt_access_cookie_key == "access_token_cookie"
        assert settings.authjwt_refresh_cookie_key == "refresh_token_cookie"
        assert settings.authjwt_access_csrf_header_name == "X-CSRF-ACCESS"
        assert settings.authjwt_refresh_csrf_header_name == "X-CSRF-REFRESH"
