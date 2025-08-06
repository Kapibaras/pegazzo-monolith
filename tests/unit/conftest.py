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
def client():
    """Client without JWT authentication."""
    app.dependency_overrides = MOCK_LINKING
    return TestClient(app)


@pytest.fixture
def authorized_client():
    """Client with valid JWT cookie for user 'adminuser' role 'administrator'."""
    app.dependency_overrides = MOCK_LINKING
    client_instance = TestClient(app)

    authorize = AuthJWT()
    access_token, refresh_token = AuthUtils.create_access_token(
        username="adminuser",
        role="administrator",
        authorize=authorize,
    )
    client_instance.cookies.set("access_token_cookie", access_token)
    client_instance.cookies.set("refresh_token_cookie", refresh_token)

    return client_instance
