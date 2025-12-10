from unittest.mock import patch

import pytest

from app.enum.auth import Role
from app.schemas.user import ActionSuccess, PermissionsResponse


@pytest.mark.usefixtures("authorized_client", "client")
class TestAuthRouter:
    """Tests for the internal AuthRouter endpoints."""

    @patch("app.services.auth.AuthService.get_permissions")
    def test_get_permissions(self, mock_get_permissions, authorized_client):
        """Test permissions endpoint returns user permissions."""
        # Arrange
        mock_get_permissions.return_value = {
            "role": "administrador",
            "permissions": ["create_user", "delete_user"],
        }

        # Act
        response = authorized_client.get("/pegazzo/internal/auth/permissions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "administrador"
        assert data["permissions"] == ["create_user", "delete_user"]
        assert PermissionsResponse.model_validate(data)
        mock_get_permissions.assert_called_once()

    @patch("app.utils.auth.AuthUtils.verify_password", return_value=True)
    def test_login_success(self, mock_verify_password, client):
        """Test login endpoint."""
        # Arrange
        user_data = {"username": "testuser", "password": "password123", "role": Role.OWNER}

        # Act
        response = client.post("/pegazzo/internal/auth/login", json=user_data)

        # Assert
        assert response.status_code == 200
        assert response.cookies.get("access_token_cookie")
        assert response.cookies.get("refresh_token_cookie")
        data = response.json()
        assert data["message"] == "Successful login"
        assert ActionSuccess.model_validate(data)
        mock_verify_password.assert_called_once_with("password123", "hashed_password")

    def test_refresh_token(self, client):
        """Test refresh token endpoint with real logic to verify cookies."""
        # Arrange
        user_data = {"username": "testuser", "password": "password123", "role": Role.OWNER}

        with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
            login_response = client.post("/pegazzo/internal/auth/login", json=user_data)

        assert login_response.status_code == 200

        # Act
        access_cookie = login_response.cookies.get("access_token_cookie")
        refresh_cookie = login_response.cookies.get("refresh_token_cookie")
        csrf_access_cookie = login_response.cookies.get("csrf_access_token")
        csrf_refresh_cookie = login_response.cookies.get("csrf_refresh_token")

        assert access_cookie
        assert refresh_cookie
        assert csrf_access_cookie
        assert csrf_refresh_cookie

        # Act
        cookies = {
            "access_token_cookie": access_cookie,
            "refresh_token_cookie": refresh_cookie,
        }

        headers = {
            "X-CSRF-ACCESS": csrf_access_cookie,
            "X-CSRF-REFRESH": csrf_refresh_cookie,
        }

        response = client.post("/pegazzo/internal/auth/refresh", cookies=cookies, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.cookies.get("access_token_cookie") is not None
        assert response.cookies.get("refresh_token_cookie") is not None

        data = response.json()
        assert data["message"] == "Token refreshed successfully"
        assert ActionSuccess.model_validate(data)

    @patch("app.services.auth.AuthService.logout")
    def test_logout(self, mock_logout, client):
        """Test logout endpoint."""
        # Act
        response = client.post("/pegazzo/internal/auth/logout")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successful logout"
        assert ActionSuccess.model_validate(data)
        mock_logout.assert_called_once()
