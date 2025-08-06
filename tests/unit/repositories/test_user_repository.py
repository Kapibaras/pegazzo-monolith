from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.errors.database import DBOperationError
from app.models.users import Role, User
from app.repositories.user import UserRepository
from app.schemas.user import RoleEnum


@pytest.fixture
def sample_user():
    """Create a sample user object for testing."""
    user = User()
    user.username = "testuser"
    user.name = "Test"
    user.surnames = "User"
    user.password = "hashed_password"
    user.role_id = 1
    return user


@pytest.fixture
def sample_role():
    """Create a sample role object for testing."""
    role = Role()
    role.id = 1
    role.name = "ADMIN"
    return role


@pytest.fixture
def user_repository_test_setup(request):
    """Fixture to set up UserRepository for class-based tests."""
    mock_db = Mock(spec=Session)
    repository = UserRepository(mock_db)
    mock_query = Mock()
    mock_filter = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_query.filter_by.return_value = mock_filter
    request.cls.repository = repository
    request.cls.mock_db = mock_db
    request.cls.mock_query = mock_query
    request.cls.mock_filter = mock_filter


@pytest.mark.usefixtures("user_repository_test_setup")
class TestUserRepository:
    """Base class for UserRepository tests."""

    def test_get_by_username(self, sample_user):
        """Test getting a user by username when user exists."""
        # Mock
        self.mock_filter.first.return_value = sample_user

        # Act
        result = self.repository.get_by_username("testuser")

        # Assert
        self.mock_db.query.assert_called_once_with(User)
        called_arg = self.mock_query.filter.call_args[0][0]
        assert called_arg.compare(User.username == "testuser")
        self.mock_filter.first.assert_called_once()
        assert result == sample_user

    def test_get_all_users(self):
        """Test getting all users."""
        # Mock
        sample_users = [User(), User()]
        sample_users[0].username = "user1"
        sample_users[1].username = "user2"
        self.mock_query.all.return_value = sample_users

        # Act
        result = self.repository.get_all_users()

        # Assert
        self.mock_db.query.assert_called_once_with(User)
        self.mock_query.all.assert_called_once()
        assert result == sample_users

    def test_get_role_by_name(self, sample_role):
        """Test getting a role by name."""
        # Mock
        self.mock_filter.first.return_value = sample_role

        # Act
        result = self.repository.get_role_by_name(RoleEnum.ADMIN)

        # Assert
        self.mock_db.query.assert_called_once_with(Role)
        self.mock_query.filter_by.assert_called_once_with(name="administrator")
        self.mock_filter.first.assert_called_once()
        assert result == sample_role

    def test_create_user_success(self, sample_user):
        """Test successful user creation."""
        # Mock
        self.repository.get_by_username = Mock(return_value=sample_user)

        # Act
        result = self.repository.create_user(sample_user)

        # Assert
        self.mock_db.add.assert_called_once_with(sample_user)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(sample_user)
        self.repository.get_by_username.assert_called_once_with("testuser")
        assert result == sample_user

    def test_create_user_failure(self, sample_user):
        """Test user creation failure raises DBOperationError."""
        # Mock
        self.mock_db.add.side_effect = Exception("DB Error")

        # Act & Assert
        with pytest.raises(DBOperationError):
            self.repository.create_user(sample_user)

        self.mock_db.rollback.assert_called_once()

    def test_update_user_success(self, sample_user):
        """Test successful user update."""
        # Mock
        self.repository.get_by_username = Mock(return_value=sample_user)

        # Act
        result = self.repository.update_user(sample_user)

        # Assert
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(sample_user)
        self.repository.get_by_username.assert_called_once_with("testuser")
        assert result == sample_user

    def test_update_user_failure(self, sample_user):
        """Test update failure raises DBOperationError."""
        # Mock
        self.mock_db.commit.side_effect = Exception("Update error")

        # Act & Assert
        with pytest.raises(DBOperationError):
            self.repository.update_user(sample_user)

        self.mock_db.rollback.assert_called_once()

    def test_delete_user_success(self, sample_user):
        """Test successful user deletion."""
        # Act
        self.repository.delete_user(sample_user)

        # Assert
        self.mock_db.delete.assert_called_once_with(sample_user)
        self.mock_db.commit.assert_called_once()

    def test_delete_user_failure(self, sample_user):
        """Test deletion failure raises DBOperationError."""
        # Mock
        self.mock_db.delete.side_effect = Exception("Delete failed")

        # Act & Assert
        with pytest.raises(DBOperationError):
            self.repository.delete_user(sample_user)

        self.mock_db.rollback.assert_called_once()
