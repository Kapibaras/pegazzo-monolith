from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.database.events
from app.dependencies import RepositoryFactory
from app.enum.auth import Role
from app.main import app
from app.models.users import User
from tests.mocks import (
    AssociateRepositoryMock,
    BalanceRepositoryMock,
    CarModelRepositoryMock,
    CarRepositoryMock,
    DocumentRepositoryMock,
    ImageRepositoryMock,
    InsuranceRepositoryMock,
    UserRepositoryMock,
)

user_repo_mock = UserRepositoryMock()
_initial_user = user_repo_mock.users[0]

balance_repo_mock = BalanceRepositoryMock()
insurance_repo_mock = InsuranceRepositoryMock()
associate_repo_mock = AssociateRepositoryMock()
car_repo_mock = CarRepositoryMock()
car_model_repo_mock = CarModelRepositoryMock()
document_repo_mock = DocumentRepositoryMock()
image_repo_mock = ImageRepositoryMock()


@pytest.fixture(autouse=True)
def disable_metrics_listener(monkeypatch):
    monkeypatch.setattr(
        "app.database.events.transaction_metrics_after_flush",
        lambda *_args, **_kwargs: None,
    )


@pytest.fixture(autouse=True)
def reset_state():
    user_repo_mock.users = [_initial_user]
    balance_repo_mock.reset()
    insurance_repo_mock.reset()
    associate_repo_mock.reset()
    car_repo_mock.reset()
    car_model_repo_mock.reset()
    document_repo_mock.reset()
    image_repo_mock.reset()


def _dependency_overrides():
    return {
        RepositoryFactory.user_repository: lambda: user_repo_mock,
        RepositoryFactory.balance_repository: lambda: balance_repo_mock,
        RepositoryFactory.insurance_repository: lambda: insurance_repo_mock,
        RepositoryFactory.associate_repository: lambda: associate_repo_mock,
        RepositoryFactory.car_repository: lambda: car_repo_mock,
        RepositoryFactory.car_model_repository: lambda: car_model_repo_mock,
        RepositoryFactory.document_repository: lambda: document_repo_mock,
        RepositoryFactory.image_repository: lambda: image_repo_mock,
    }


def _attach_repos(client):
    client.balance_repo = balance_repo_mock
    client.user_repo = user_repo_mock
    client.insurance_repo = insurance_repo_mock
    client.associate_repo = associate_repo_mock
    client.car_repo = car_repo_mock
    client.car_model_repo = car_model_repo_mock
    client.document_repo = document_repo_mock
    client.image_repo = image_repo_mock


@pytest.fixture
def client():
    """Client without JWT authentication."""
    app.dependency_overrides = _dependency_overrides()
    c = TestClient(app)
    _attach_repos(c)
    return c


@pytest.fixture
def authorized_client():
    """Client with valid JWT cookie for role 'owner'."""
    app.dependency_overrides = _dependency_overrides()

    c = TestClient(app)
    _attach_repos(c)

    with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
        response = c.post(
            "/pegazzo/internal/auth/login",
            json={"username": "testuser", "password": "password123", "role": Role.OWNER},
        )

    c.cookies.set("access_token_cookie", response.cookies.get("access_token_cookie"))
    c.cookies.set("refresh_token_cookie", response.cookies.get("refresh_token_cookie"))
    c.headers.update(
        {
            "X-CSRF-ACCESS": response.cookies.get("csrf_access_token"),
            "X-CSRF-REFRESH": response.cookies.get("csrf_refresh_token"),
        },
    )

    return c


@pytest.fixture
def admin_authorized_client():
    """Client with valid JWT cookie for role 'admin'."""
    app.dependency_overrides = _dependency_overrides()

    admin_user = User(
        username="adminuser",
        name="Admin",
        surnames="User",
        password="hashed_password",
        role_id=2,
        role=user_repo_mock.roles["administrador"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    user_repo_mock.users.append(admin_user)

    c = TestClient(app)
    _attach_repos(c)

    with patch("app.utils.auth.AuthUtils.verify_password", return_value=True):
        response = c.post(
            "/pegazzo/internal/auth/login",
            json={"username": "adminuser", "password": "password123"},
        )

    c.cookies.set("access_token_cookie", response.cookies.get("access_token_cookie"))
    c.cookies.set("refresh_token_cookie", response.cookies.get("refresh_token_cookie"))
    c.headers.update(
        {
            "X-CSRF-ACCESS": response.cookies.get("csrf_access_token"),
            "X-CSRF-REFRESH": response.cookies.get("csrf_refresh_token"),
        },
    )

    return c
