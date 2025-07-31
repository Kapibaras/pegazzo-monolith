from fastapi import Depends

from app.services import UserService

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
