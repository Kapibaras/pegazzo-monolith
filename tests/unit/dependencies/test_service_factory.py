from unittest.mock import patch

from app.dependencies import ServiceFactory
from app.services import AuthService, UserService


class TestServiceFactory:
    """Clase de pruebas para la factoría de servicios."""

    @patch("app.dependencies.service_factory.RepositoryFactory.user_repository")
    def test_user_service(self, mock_user_repository):
        service_generator = ServiceFactory.user_service(mock_user_repository)
        service = next(service_generator)

        assert isinstance(service, UserService)
        assert service.repository == mock_user_repository

    @patch("app.dependencies.service_factory.RepositoryFactory.user_repository")
    @patch("app.dependencies.service_factory.AuthJWT")
    def test_auth_service(self, mock_authjwt, mock_user_repository):
        service_generator = ServiceFactory.auth_service(mock_authjwt, mock_user_repository)
        service = next(service_generator)

        assert isinstance(service, AuthService)
        assert service.authorize == mock_authjwt
        assert service.repository == mock_user_repository
