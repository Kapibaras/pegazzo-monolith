from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthRouter:
    """Unit tests for the /health endpoint."""

    @patch("app.routers.health._check_broker", new_callable=AsyncMock, return_value="ok")
    @patch("app.routers.health._check_db", new_callable=AsyncMock, return_value="ok")
    def test_health_ok(self, _mock_db, _mock_broker, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok", "broker": "ok"}

    @patch("app.routers.health._check_broker", new_callable=AsyncMock, return_value="ok")
    @patch("app.routers.health._check_db", new_callable=AsyncMock, return_value="unreachable")
    def test_health_db_unreachable(self, _mock_db, _mock_broker, client):
        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"status": "error", "database": "unreachable", "broker": "ok"}

    @patch("app.routers.health._check_broker", new_callable=AsyncMock, return_value="unreachable")
    @patch("app.routers.health._check_db", new_callable=AsyncMock, return_value="ok")
    def test_health_broker_unreachable_is_degraded(self, _mock_db, _mock_broker, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "degraded", "database": "ok", "broker": "unreachable"}

    @patch("app.routers.health._check_broker", new_callable=AsyncMock, return_value="unreachable")
    @patch("app.routers.health._check_db", new_callable=AsyncMock, return_value="unreachable")
    def test_health_db_unreachable_still_checks_broker(self, _mock_db, _mock_broker, client):
        response = client.get("/health")

        assert response.status_code == 503
        body = response.json()
        assert body["broker"] == "unreachable"
        assert body["status"] == "error"
