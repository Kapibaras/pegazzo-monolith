from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import RepositoryFactory
from app.main import app
from app.schemas.user import RoleEnum
from tests.mocks import UserRepositoryMock

MOCK_LINKING = {
    RepositoryFactory.user_repository: lambda: UserRepositoryMock(),
}


@pytest.fixture(scope="session")
def client():
    """Client without JWT authentication."""
    app.dependency_overrides = MOCK_LINKING
    return TestClient(app)


@pytest.fixture(scope="session")
def authorized_client():
    """Client with valid JWT cookie for user 'adminuser' role 'administrator'."""
    app.dependency_overrides = MOCK_LINKING
    client_instance = TestClient(app)

    with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
        response = client_instance.post(
            "/pegazzo/internal/auth/login",
            json={"username": "testuser", "password": "password123", "role": RoleEnum.ADMIN},
        )

    client_instance.cookies.set("access_token_cookie", response.cookies.get("access_token_cookie"))
    client_instance.cookies.set("refresh_token_cookie", response.cookies.get("refresh_token_cookie"))
    client_instance.headers.update(
        {
            "X-CSRF-ACCESS": response.cookies.get("csrf_access_token"),
            "X-CSRF-REFRESH": response.cookies.get("csrf_refresh_token"),
        },
    )

    return client_instance
