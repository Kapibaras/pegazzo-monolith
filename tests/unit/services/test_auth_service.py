from unittest.mock import Mock, patch

import pytest

from app.auth import Role
from app.errors.auth import InvalidCredentials, InvalidRefreshToken
from app.errors.user import UserNotFoundException
from app.models.users import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService


@pytest.fixture
def auth_service_test_setup(request):
    """Fixture to set up AuthService with mocked dependencies."""
    mock_authorize = Mock()
    mock_repository = Mock(spec=UserRepository)
    service = AuthService(authorize=mock_authorize, repository=mock_repository)
    request.cls.service = service
    request.cls.mock_authorize = mock_authorize
    request.cls.mock_repo = mock_repository


@pytest.mark.usefixtures("auth_service_test_setup")
class TestAuthService:
    """Unit tests for AuthService."""

    @patch("app.services.auth.AuthUtils.verify_password", return_value=True)
    @patch("app.services.auth.AuthUtils.create_access_token", return_value=("access_token", "refresh_token"))
    def test_login_success(self, mock_create_token, mock_verify_password):
        """Test successful login sets cookies correctly."""
        # Arrange
        user = User(username="testuser", password="hashed", role=Role.OWNER)
        self.mock_repo.get_by_username.return_value = user

        # Act
        result = self.service.login("testuser", "password123")

        # Assert
        self.mock_repo.get_by_username.assert_called_once_with("testuser")
        mock_verify_password.assert_called_once_with("password123", "hashed")
        mock_create_token.assert_called_once()
        self.mock_authorize.set_access_cookies.assert_called_once_with("access_token")
        self.mock_authorize.set_refresh_cookies.assert_called_once_with("refresh_token")
        assert result is None

    def test_login_user_not_found(self):
        """Test login with nonexistent user raises UserNotFoundException."""
        self.mock_repo.get_by_username.return_value = None
        with pytest.raises(UserNotFoundException):
            self.service.login("nouser", "password123")

    @patch("app.services.auth.AuthUtils.verify_password", return_value=False)
    def test_login_invalid_password(self, _):
        """Test login with wrong password raises InvalidCredentials."""
        self.mock_repo.get_by_username.return_value = User(username="testuser", password="hashed", role=Role.EMPLOYEE)
        with pytest.raises(InvalidCredentials):
            self.service.login("testuser", "wrongpass")

    @patch("app.services.auth.AuthUtils.create_access_token", return_value=("new_access", "new_refresh"))
    def test_refresh_success(self, mock_create_token):
        """Test successful refresh generates new tokens and sets them."""
        # Arrange
        self.mock_authorize.get_jwt_subject.return_value = "testuser"
        self.mock_authorize.get_raw_jwt.return_value = {"role": Role.OWNER}

        # Act
        result = self.service.refresh()

        # Assert
        self.mock_authorize.jwt_refresh_token_required.assert_called_once()
        self.mock_authorize.get_jwt_subject.assert_called_once()
        self.mock_authorize.get_raw_jwt.assert_called_once()
        mock_create_token.assert_called_once_with(username="testuser", role=Role.OWNER, authorize=self.mock_authorize)
        self.mock_authorize.set_access_cookies.assert_called_once_with("new_access")
        self.mock_authorize.set_refresh_cookies.assert_called_once_with("new_refresh")
        assert result is None

    def test_refresh_invalid_token(self):
        """Test refresh with missing/invalid token raises exception."""
        self.mock_authorize.jwt_refresh_token_required.side_effect = Exception("Invalid token")
        with pytest.raises(InvalidRefreshToken):
            self.service.refresh()

    def test_logout(self):
        """Test logout unsets JWT cookies."""
        # Act
        result = self.service.logout()

        # Assert
        self.mock_authorize.unset_jwt_cookies.assert_called_once()
        assert result is None

    def test_get_current_user_returns_user(self):
        """Test get_current_user returns the user from the repository."""
        # Arrange
        mock_user = Mock(spec=User)
        self.mock_authorize.get_jwt_subject.return_value = "JuanOvando"
        self.mock_repo.get_by_username.return_value = mock_user

        # Act
        result = self.service.get_current_user()

        # Assert
        self.mock_authorize.get_jwt_subject.assert_called_once()
        self.mock_repo.get_by_username.assert_called_once_with("JuanOvando")
        assert result == mock_user

    def test_get_permissions_returns_role_and_permissions(self):
        """Test get_permissions returns role and permissions of current user."""
        # Arrange
        mock_perm1 = Mock()
        mock_perm1.name = "create_user"
        mock_perm2 = Mock()
        mock_perm2.name = "delete_user"

        mock_role = Mock()
        mock_role.name = "administrador"
        mock_role.permissions = [mock_perm1, mock_perm2]

        mock_user = Mock()
        mock_user.role = mock_role

        self.mock_authorize.get_jwt_subject.return_value = "JuanOvando"
        self.mock_repo.get_by_username.return_value = mock_user

        # Act
        result = self.service.get_permissions()

        # Assert
        self.mock_authorize.get_jwt_subject.assert_called_once()
        self.mock_repo.get_by_username.assert_called_once_with("JuanOvando")
        assert result == {"role": "administrador", "permissions": ["create_user", "delete_user"]}
