from fastapi import Depends
from fastapi_jwt_auth import AuthJWT

from app.services import AuthService, BalanceService, UserService

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
