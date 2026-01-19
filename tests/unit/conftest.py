import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.database.events
from app.database.base import Base
from app.dependencies import RepositoryFactory
from app.enum.auth import Role
from app.main import app
from tests.mocks import UserRepositoryMock
from tests.mocks.balance_repository_mock import BalanceRepositoryMock
from tests.unit.utils.test_errors_util import MissingDatabaseURLError

user_repo_mock = UserRepositoryMock()
initial_user = user_repo_mock.users[0]

balance_repo_mock = BalanceRepositoryMock()
initial_transaction = balance_repo_mock.transactions[0]


class DummyDBSession:
    """Dummy DB session para Depends."""

    def rollback(self):
        pass

    def close(self):
        pass


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


@pytest.fixture
def metrics_db_session():
    """Session Postgres (Docker)."""
    if not os.getenv("DATABASE_URL"):
        raise MissingDatabaseURLError

    engine = create_engine(os.getenv("DATABASE_URL"), future=True)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    try:
        session.execute(text("TRUNCATE transaction_metrics RESTART IDENTITY CASCADE;"))
        session.execute(text('TRUNCATE "transaction" CASCADE;'))
        session.commit()

        yield session
    finally:
        session.rollback()
        session.close()
