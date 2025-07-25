from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.models.users import User
from app.repositories.user import UserRepository


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


@pytest.fixture(scope="function")
def user_repository_test_setup(request):
    """Fixture to set up UserRepository for class-based tests."""
    mock_db = Mock(spec=Session)
    repository = UserRepository(mock_db)
    mock_query = Mock()
    mock_filter = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    # Assign the repository and mock_db to the test class
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

    def test_create_user(self, sample_user):
        """Test creating a new user."""
        # Act
        result = self.repository.create_user(sample_user)

        # Assert
        self.mock_db.add.assert_called_once_with(sample_user)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(sample_user)
        assert result == sample_user
