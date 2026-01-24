from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.database.events
from app.dependencies import RepositoryFactory
from app.enum.auth import Role
from app.main import app
from tests.mocks import UserRepositoryMock
from tests.mocks.balance_repository_mock import BalanceRepositoryMock

user_repo_mock = UserRepositoryMock()
initial_user = user_repo_mock.users[0]

balance_repo_mock = BalanceRepositoryMock()
initial_transaction = balance_repo_mock.transactions[0]


@pytest.fixture(autouse=True)
def disable_metrics_listener(monkeypatch):
    monkeypatch.setattr(
        "app.database.events.transaction_metrics_after_flush",
        lambda *_args, **_kwargs: None,
    )


@pytest.fixture(autouse=True)
def reset_state():
    user_repo_mock.users = [initial_user]
    balance_repo_mock.transactions = [initial_transaction]


@pytest.fixture(scope="session")
def client():
    """Client without JWT authentication."""
    app.dependency_overrides = {
        RepositoryFactory.user_repository: lambda: user_repo_mock,
        RepositoryFactory.balance_repository: lambda: balance_repo_mock,
    }
    return TestClient(app)


@pytest.fixture(scope="session")
def authorized_client():
    """Client with valid JWT cookie for user 'owneruser' role 'owner'."""
    app.dependency_overrides = {
        RepositoryFactory.user_repository: lambda: user_repo_mock,
        RepositoryFactory.balance_repository: lambda: balance_repo_mock,
    }

    client = TestClient(app)

    with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
        response = client.post(
            "/pegazzo/internal/auth/login",
            json={"username": "testuser", "password": "password123", "role": Role.OWNER},
        )

    client.cookies.set("access_token_cookie", response.cookies.get("access_token_cookie"))
    client.cookies.set("refresh_token_cookie", response.cookies.get("refresh_token_cookie"))
    client.headers.update(
        {
            "X-CSRF-ACCESS": response.cookies.get("csrf_access_token"),
            "X-CSRF-REFRESH": response.cookies.get("csrf_refresh_token"),
        },
    )

    return client
