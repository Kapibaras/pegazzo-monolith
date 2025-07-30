from fastapi import Depends

from app.database import get_db
from app.repositories import UserRepository


class RepositoryFactory:
    """Factory class to provide repository instances with dependency injection."""

    @staticmethod
    def user_repository(db_session=Depends(get_db)):
        """Provide an instance of UserRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:UserRepository: An instance of UserRepository initialized with the provided database session.
        """

        yield UserRepository(db_session)
