from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthRouter:
    """Unit tests for the /health endpoint."""

    @patch("app.routers.health._check_broker", return_value="ok")
    @patch("app.routers.health.test_connection")
    def test_health_ok(self, mock_test_connection, mock_broker, client):
        mock_test_connection.return_value = None

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok", "broker": "ok"}

    @patch("app.routers.health._check_broker", return_value="ok")
    @patch("app.routers.health.test_connection")
    def test_health_db_unreachable(self, mock_test_connection, mock_broker, client):
        mock_test_connection.side_effect = RuntimeError("DB down")

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"status": "error", "database": "unreachable", "broker": "unknown"}

    @patch("app.routers.health._check_broker", return_value="unreachable")
    @patch("app.routers.health.test_connection")
    def test_health_broker_unreachable_is_non_fatal(self, mock_test_connection, mock_broker, client):
        mock_test_connection.return_value = None

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok", "broker": "unreachable"}
