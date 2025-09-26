from datetime import timedelta

import pytest

from app.auth.core import Settings


@pytest.fixture
def env_vars(monkeypatch):
    """Fixture that simulates environment variables for JWT configuration."""
    monkeypatch.setenv("JWT_SECRET_KEY", "testsecret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7")
    monkeypatch.setenv("ENVIRONMENT", "LOCAL")


@pytest.fixture
def settings(env_vars):
    """Fixture that returns a Settings instance with mocked variables."""

    _ = env_vars
    return Settings()


class TestAuthJWTSettings:
    """Class of tests for AuthJWT configuration."""

    def test_settings_instance(self, settings):
        assert isinstance(settings, Settings)

    def test_settings_values(self, settings):
        assert settings.authjwt_secret_key == "top_secret"
        assert settings.authjwt_token_location == {"cookies"}
        assert settings.authjwt_cookie_csrf_protect is True
        assert settings.authjwt_cookie_secure is True
        assert settings.authjwt_cookie_samesite == "lax"
        assert settings.authjwt_cookie_httponly is True
        assert settings.authjwt_access_token_expires == timedelta(minutes=15)
        assert settings.authjwt_refresh_token_expires == timedelta(days=7)
        assert settings.authjwt_access_cookie_key == "access_token_cookie"
        assert settings.authjwt_refresh_cookie_key == "refresh_token_cookie"
        assert settings.authjwt_access_csrf_header_name == "X-CSRF-ACCESS"
        assert settings.authjwt_refresh_csrf_header_name == "X-CSRF-REFRESH"
