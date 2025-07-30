from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.models.users import User
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
    user.role = RoleEnum.admin
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
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
    request.cls.repository = repository
    request.cls.mock_db = mock_db
    request.cls.mock_query = mock_query
    request.cls.mock_filter = mock_filter


@pytest.mark.usefixtures("user_repository_test_setup")
class TestUserRepositoryMock:
    def test_get_by_username(self, user_repository_mock, sample_user):
        user_repository_mock.create_user(sample_user)
        result = user_repository_mock.get_by_username("testuser")
        assert result is not None
        assert result.username == "testuser"

    def test_get_all_users(self, user_repository_mock, sample_user):
        user_repository_mock.create_user(sample_user)
        users = user_repository_mock.get_all_users()
        assert len(users) > 0

    def test_create_user_duplicate_raises(self, user_repository_mock, sample_user):
        user_repository_mock.create_user(sample_user)
        with pytest.raises(Exception):
            user_repository_mock.create_user(sample_user)

    def test_update_user(self, user_repository_mock, sample_user):
        user_repository_mock.create_user(sample_user)
        sample_user.name = "Updated"
        updated = user_repository_mock.update_user(sample_user)
        assert updated.name == "Updated"

    def test_delete_user(self, user_repository_mock, sample_user):
        user_repository_mock.create_user(sample_user)
        user_repository_mock.delete_user(sample_user)
        assert sample_user in user_repository_mock._deleted_users
