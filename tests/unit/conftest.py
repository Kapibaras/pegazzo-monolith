import pytest
from fastapi.testclient import TestClient

from app.dependencies import RepositoryFactory
from app.main import app
from tests.mocks import UserRepositoryMock

MOCK_LINKING = {RepositoryFactory.user_repository: lambda: UserRepositoryMock()}


@pytest.fixture(scope="class")
def client(request):
    app.dependency_overrides = MOCK_LINKING
    request.cls.client = TestClient(app)
