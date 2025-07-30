from unittest.mock import Mock, patch

import pytest

from app.models.users import User
from app.repositories.user import UserRepository
from app.services.user import UserService


@pytest.fixture(scope="function")
def user_service_test_setup(request):
    """Fixture to set up UserRepository for class-based tests."""
    mock_repo = Mock(spec=UserRepository)
    service = UserService(mock_repo)
    request.cls.service = service
    request.cls.mock_repo = mock_repo


@pytest.mark.usefixtures("user_service_test_setup")
class TestUserService:
    """Base class for UserService tests."""

    def test_get_user(self):
        """Test getting a user by username."""
        # Arrange
        self.mock_repo.get_by_username.return_value = User(username="testuser")
        # Act
        result = self.service.get_user("testuser")
        # Assert
        self.mock_repo.get_by_username.assert_called_once_with("testuser")
        assert result.username == "testuser"

    def test_get_all_users(self):
        """Test getting all users."""
        # Arrange
        self.mock_repo.get_all_users.return_value = [
            User(username="user1"),
            User(username="user2"),
        ]
        # Act
        result = self.service.get_all_users()
        # Assert
        self.mock_repo.get_all_users.assert_called_once()
        assert len(result) == 2
        assert result[0].username == "user1"
        assert result[1].username == "user2"

    @patch("app.services.user.User")
    def test_create_user(self, mock_user_class):
        """Test creating a new user."""
        # Arrange
        user_data = {
            "username": "testuser",
            "name": "Test",
            "surnames": "User",
            "password": "password123",
            "role": "user",
        }
        new_user = User(**user_data)
        mock_user_class.return_value = new_user
        self.mock_repo.create_user.return_value = new_user

        # Act
        result = self.service.create_user(**user_data)

        # Assert
        self.mock_repo.create_user.assert_called_once_with(new_user)
        assert result.username == "newuser"
