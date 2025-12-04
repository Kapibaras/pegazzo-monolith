from fastapi import Depends

from app.database import get_db
from app.repositories import BalanceRepository, UserRepository


class RepositoryFactory:
    """Factory class to provide repository instances with dependency injection."""

    @staticmethod
    def user_repository(db_session=Depends(get_db)):
        """Provide an instance of UserRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:UserRepository: An instance of UserRepository initialized with the provided database session.
        """

        yield UserRepository(db_session)

    @staticmethod
    def balance_repository(db_session=Depends(get_db)):
        """Provide an instance of BalanceRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:BalanceRepository: An instance of BalanceRepository initialized with the provided database session.
        """

        yield BalanceRepository(db_session)
