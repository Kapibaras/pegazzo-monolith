from unittest.mock import patch

import pytest

from app.schemas.user import ActionSuccess, RoleEnum


@pytest.mark.usefixtures("client")
class TestAuthRouter:
    """Tests for the internal AuthRouter endpoints."""

    @patch("app.utils.auth.AuthUtils.verify_password", return_value=True)
    def test_login_success(self, mock_verify_password, client):
        """Test login endpoint."""
        # Arrange
        user_data = {"username": "testuser", "password": "password123", "role": RoleEnum.ADMIN}

        # Act
        response = client.post("/pegazzo/internal/auth/login", json=user_data)

        # Assert
        assert response.status_code == 200
        assert response.cookies.get("access_token_cookie")
        assert response.cookies.get("refresh_token_cookie")
        data = response.json()
        assert data["message"] == "Successful login"
        assert ActionSuccess.validate(data)
        mock_verify_password.assert_called_once_with("password123", "hashed_password")

    def test_refresh_token(self, client):
        """Test refresh token endpoint with real logic to verify cookies."""
        # Arrange
        user_data = {"username": "testuser", "password": "password123", "role": RoleEnum.ADMIN}

        with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
            login_response = client.post("/pegazzo/internal/auth/login", json=user_data)

        assert login_response.status_code == 200

        # Act
        access_cookie = login_response.cookies.get("access_token_cookie")
        refresh_cookie = login_response.cookies.get("refresh_token_cookie")

        assert access_cookie
        assert refresh_cookie

        # Act
        cookies = {
            "access_token_cookie": access_cookie,
            "refresh_token_cookie": refresh_cookie,
        }

        response = client.post("/pegazzo/internal/auth/refresh", cookies=cookies)

        # Assert
        assert response.status_code == 200
        assert response.cookies.get("access_token_cookie") is not None
        assert response.cookies.get("refresh_token_cookie") is not None

        data = response.json()
        assert data["message"] == "Token refreshed successfully"
        assert ActionSuccess.validate(data)

    @patch("app.services.auth.AuthService.logout")
    def test_logout(self, mock_logout, client):
        """Test logout endpoint."""
        # Act
        response = client.post("/pegazzo/internal/auth/logout")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successful logout"
        assert ActionSuccess.validate(data)
        mock_logout.assert_called_once()
