from unittest.mock import patch

import pytest

from app.schemas.user import ActionSuccess


@pytest.mark.usefixtures("client")
class TestAuthRouter:
    """Tests for the internal AuthRouter endpoints."""

    @patch("app.services.auth.AuthService.login")
    def test_login_success(self, mock_login):
        """Test login endpoint."""
        # Arrange
        user_data = {"username": "testuser", "password": "password123"}

        # Act
        response = self.client.post("/pegazzo/internal/auth/login", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert ActionSuccess.validate(data)
        mock_login.assert_called_once_with(user_data["username"], user_data["password"])

    @patch("app.services.auth.AuthService.refresh")
    def test_refresh_token(self, mock_refresh):
        """Test refresh token endpoint."""
        # Act
        response = self.client.post("/pegazzo/internal/auth/refresh")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Token refreshed successfully"
        assert ActionSuccess.validate(data)
        mock_refresh.assert_called_once()

    @patch("app.services.auth.AuthService.logout")
    def test_logout(self, mock_logout):
        """Test logout endpoint."""
        # Act
        response = self.client.post("/pegazzo/internal/auth/logout")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"
        assert ActionSuccess.validate(data)
        mock_logout.assert_called_once()
