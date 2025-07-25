from unittest.mock import patch

from app.dependencies import ServiceFactory
from app.services import UserService


class TestServiceFactory:

    @patch("app.dependencies.service_factory.RepositoryFactory.user_repository")
    def test_user_service(self, mock_user_repository):
        service_generator = ServiceFactory.user_service(mock_user_repository)
        service = next(service_generator)

        assert isinstance(service, UserService)
        assert service.repository == mock_user_repository
