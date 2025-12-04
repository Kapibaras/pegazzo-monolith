from unittest.mock import patch

from app.dependencies import RepositoryFactory
from app.repositories import BalanceRepository, UserRepository


@patch("app.dependencies.repository_factory.get_db")
class TestRepositoryFactory:
    """Class of tests for the repository factory."""

    def test_user_repository(self, mock_get_db):
        repository_generator = RepositoryFactory.user_repository(mock_get_db)
        repository = next(repository_generator)

        assert isinstance(repository, UserRepository)
        assert repository.db == mock_get_db

    def test_balance_repository(self, mock_get_db):
        repository_generator = RepositoryFactory.balance_repository(mock_get_db)
        repository = next(repository_generator)

        assert isinstance(repository, BalanceRepository)
        assert repository.db == mock_get_db
