from fastapi import Depends

from app.database import get_db
from app.repositories import AssociateRepository, BalanceRepository, CarRepository, DocumentRepository, InsuranceRepository, UserRepository


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

    @staticmethod
    def insurance_repository(db_session=Depends(get_db)):
        """Provide an instance of InsuranceRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:InsuranceRepository: An instance of InsuranceRepository initialized with the provided database session.
        """

        yield InsuranceRepository(db_session)

    @staticmethod
    def associate_repository(db_session=Depends(get_db)):
        """Provide an instance of AssociateRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:AssociateRepository: An instance of AssociateRepository initialized with the provided database session.
        """

        yield AssociateRepository(db_session)

    @staticmethod
    def car_repository(db_session=Depends(get_db)):
        """Provide an instance of CarRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:CarRepository: An instance of CarRepository initialized with the provided database session.
        """

        yield CarRepository(db_session)

    @staticmethod
    def document_repository(db_session=Depends(get_db)):
        """Provide an instance of DocumentRepository.

        Args:db_session (Session): The database session, injected via FastAPI's Depends.

        Yields:DocumentRepository: An instance of DocumentRepository initialized with the provided database session.
        """

        yield DocumentRepository(db_session)
