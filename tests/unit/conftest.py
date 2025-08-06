import pytest
from fastapi.testclient import TestClient
from fastapi_jwt_auth import AuthJWT

from app.dependencies import RepositoryFactory
from app.main import app
from app.utils.auth import AuthUtils
from tests.mocks import UserRepositoryMock

MOCK_LINKING = {
    RepositoryFactory.user_repository: lambda: UserRepositoryMock(),
}


@pytest.fixture
def client_no_auth():
    """Client sin autenticación (usado directamente como fixture)."""
    app.dependency_overrides = MOCK_LINKING
    return TestClient(app)


@pytest.fixture(scope="class")
def client(request):
    """Client sin autenticación (puede usarse para probar accesos no autorizados)."""
    app.dependency_overrides = MOCK_LINKING
    request.cls.client_no_auth = TestClient(app)
    return request.cls.client_no_auth


@pytest.fixture(scope="class")
def authorized_client(request, client):
    """Client con cookie JWT válida para usuario 'adminuser' rol 'admin'."""
    authorize = AuthJWT()
    access_token, refresh_token = AuthUtils.create_access_token(
        username="adminuser",
        role="administrator",
        authorize=authorize,
    )
    client.cookies.set("access_token_cookie", access_token)
    client.cookies.set("refresh_token_cookie", refresh_token)
    request.cls.client = client
    return client
