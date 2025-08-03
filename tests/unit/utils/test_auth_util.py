from unittest.mock import Mock

import pytest
from argon2.exceptions import VerifyMismatchError

from app.utils.auth import AuthUtils


class TestAuthUtils:
    """Unit tests for AuthUtils."""

    def test_hash_and_verify_password_success(self):
        """Test hash and verify password success."""
        plain_password = "mypassword"
        hashed = AuthUtils.hash_password(plain_password)

        assert isinstance(hashed, str)
        assert AuthUtils.verify_password(plain_password, hashed)

    def test_verify_password_fail(self):
        """Debe fallar si la contraseña no coincide."""
        plain_password = "mypassword"
        wrong_password = "wrong"
        hashed = AuthUtils.hash_password(plain_password)

        with pytest.raises(VerifyMismatchError):
            AuthUtils.verify_password(wrong_password, hashed)

    def test_create_access_token_calls_authorize_methods(self):
        """Debe crear access y refresh tokens usando authorize."""
        mock_authorize = Mock()
        mock_authorize.create_access_token.return_value = "access"
        mock_authorize.create_refresh_token.return_value = "refresh"

        username = "testuser"
        role = "admin"

        access_token, refresh_token = AuthUtils.create_access_token(username, role, mock_authorize)

        mock_authorize.create_access_token.assert_called_once()
        mock_authorize.create_refresh_token.assert_called_once()

        assert access_token == "access"
        assert refresh_token == "refresh"
