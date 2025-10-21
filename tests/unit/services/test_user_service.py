from unittest.mock import Mock

import pytest

from app.auth import Role
from app.errors.user import RoleNotFoundException, UsernameAlreadyExistsException, UserNotFoundException
from app.models.users import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateSchema, UserUpdateSchema
from app.services.user import UserService


@pytest.fixture
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

    def test_get_user_not_found(self):
        """Test error when user is not found."""
        # Arrange
        self.mock_repo.get_by_username.return_value = None
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            self.service.get_user("nouser")

    def test_get_all_users_without_role(self):
        """Test getting all users without role filter."""
        # Arrange
        self.mock_repo.get_all_users.return_value = [
            User(username="user1"),
            User(username="user2"),
        ]
        # Act
        result = self.service.get_all_users()
        # Assert
        self.mock_repo.get_all_users.assert_called_once_with(role_id=None)
        assert len(result) == 2

    def test_get_all_users_with_role(self):
        """Test getting all users filtered by role."""
        # Arrange
        self.mock_repo.get_role_by_name.return_value = Mock(id=2)
        self.mock_repo.get_all_users.return_value = [User(username="propietario")]
        # Act
        result = self.service.get_all_users(role_name=Role.OWNER)
        # Assert
        self.mock_repo.get_role_by_name.assert_called_once_with("propietario")
        self.mock_repo.get_all_users.assert_called_once_with(role_id=2)
        assert result[0].username == "propietario"

    def test_get_all_users_role_not_found(self):
        """Test error when role does not exist."""
        # Arrange
        self.mock_repo.get_role_by_name.return_value = None
        # Act & Assert
        with pytest.raises(RoleNotFoundException):
            self.service.get_all_users(role_name=Role.OWNER)

    def test_create_user(self):
        """Test creating a new user."""
        # Arrange
        data = UserCreateSchema(username="newuser", name="Test", surnames="User", password="123456", role="propietario")

        role_mock = Mock()
        self.mock_repo.get_role_by_name.return_value = role_mock
        self.mock_repo.get_by_username.return_value = None

        self.mock_repo.create_user.side_effect = lambda user: user

        # Act
        result = self.service.create_user(data)

        # Assert
        self.mock_repo.get_role_by_name.assert_called_once_with("propietario")
        self.mock_repo.get_by_username.assert_called_once_with("newuser")
        self.mock_repo.create_user.assert_called_once()
        assert result.username == "newuser"
        assert result.role == role_mock

    def test_create_user_already_exists(self):
        """Test creating a user that already exists."""
        # Arrange
        data = UserCreateSchema(username="existinguser", name="Test", surnames="User", password="123456", role="propietario")
        self.mock_repo.get_role_by_name.return_value = Mock()
        self.mock_repo.get_by_username.return_value = User(username="existinguser")

        # Act & Assert
        with pytest.raises(UsernameAlreadyExistsException):
            self.service.create_user(data)

    def test_update_user(self):
        """Test updating an existing user."""
        # Arrange
        data = UserUpdateSchema(name="Updated", surnames="User", role="propietario")
        role_mock = Mock()
        user_mock = User(username="testuser", name="Old", surnames="Old", role=role_mock)

        self.mock_repo.get_role_by_name.return_value = role_mock
        self.mock_repo.get_by_username.return_value = user_mock

        # Act
        result = self.service.update_user("testuser", data)

        # Assert
        self.mock_repo.get_by_username.assert_called_once_with("testuser")
        self.mock_repo.update_user.assert_called_once_with(user_mock)
        assert result.name == "Updated"
        assert result.surnames == "User"
        assert result.role == role_mock

    def test_update_user_not_found(self):
        """Test error when updating a non-existent user."""
        # Arrange
        data = UserUpdateSchema(name="Name", surnames="Surnames", role="propietario")
        self.mock_repo.get_by_username.return_value = None
        self.mock_repo.get_role_by_name.return_value = Mock()

        # Act & Assert
        with pytest.raises(UserNotFoundException):
            self.service.update_user("nouser", data)

    def test_delete_user(self):
        """Test deleting a user by username."""
        # Arrange
        user_mock = User(username="todelete")
        self.mock_repo.get_by_username.return_value = user_mock

        # Act
        self.service.delete_user("todelete")

        # Assert
        self.mock_repo.get_by_username.assert_called_once_with("todelete")
        self.mock_repo.delete_user.assert_called_once_with(user_mock)

    def test_delete_user_not_found(self):
        """Test error when deleting non-existent user."""
        # Arrange
        self.mock_repo.get_by_username.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundException):
            self.service.delete_user("nouser")
