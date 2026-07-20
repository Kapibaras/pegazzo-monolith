from fastapi import Depends
from fastapi_jwt_auth import AuthJWT

from app.services import AssociateService, AuthService, BalanceService, InsuranceService, UserService

from .repository_factory import RepositoryFactory


class ServiceFactory:
    """Factory class to create service instances with dependency injection."""

    @staticmethod
    def user_service(repository=Depends(RepositoryFactory.user_repository)):
        """Provide an instance of UserService.

        Args:repository (UserRepository): An instance of UserRepository, injected via FastAPI's Depends.

        Yields:UserService: An instance of UserService initialized with the provided repository.
        """
        yield UserService(repository)

    @staticmethod
    def auth_service(authorize=Depends(AuthJWT), repository=Depends(RepositoryFactory.user_repository)):
        """Provide an instance of AuthService.

        Args:authorize (AuthJWT): An instance of AuthJWT, injected via FastAPI's Depends.

        Yields:AuthService: An instance of AuthService initialized with the provided authorize.
        """
        yield AuthService(authorize, repository)

    @staticmethod
    def balance_service(repository=Depends(RepositoryFactory.balance_repository)):
        """Provide an instance of BalaceService.

        Args:repository (BlanceRepository): An instance of BalanceRepository, injected via FastAPI's Depends.

        Yields:BalanceService: An instance of BalanceService initialized with the provided repository.
        """
        yield BalanceService(repository)

    @staticmethod
    def insurance_service(repository=Depends(RepositoryFactory.insurance_repository)):
        """Provide an instance of InsuranceService.

        Args:repository (InsuranceRepository): An instance of InsuranceRepository, injected via FastAPI's Depends.

        Yields:InsuranceService: An instance of InsuranceService initialized with the provided repository.
        """
        yield InsuranceService(repository)

    @staticmethod
    def associate_service(repository=Depends(RepositoryFactory.associate_repository)):
        """Provide an instance of AssociateService.

        Args:repository (AssociateRepository): An instance of AssociateRepository, injected via FastAPI's Depends.

        Yields:AssociateService: An instance of AssociateService initialized with the provided repository.
        """
        yield AssociateService(repository)
