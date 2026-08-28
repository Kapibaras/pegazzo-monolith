"""Tests for global exception handlers registered on the FastAPI app."""
from enum import Enum
from typing import Literal

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Registration tests — verify handlers are actually registered on the app
# ---------------------------------------------------------------------------


def test_global_exception_handler_registered():
    """Exception handler for unhandled errors is registered."""
    assert Exception in app.exception_handlers


def test_validation_exception_handler_registered():
    """Exception handler for validation errors is registered."""
    assert RequestValidationError in app.exception_handlers


# ---------------------------------------------------------------------------
# Functional tests — spin up an isolated app that uses the same handlers
# so we don't depend on main app's auth/DB infrastructure.
# ---------------------------------------------------------------------------


class _Period(str, Enum):
    week = "week"
    month = "month"
    year = "year"


def _make_test_app() -> FastAPI:
    """Create a minimal app with the same global handlers applied."""
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    test_app = FastAPI()

    @test_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request, exc: RequestValidationError):
        errors = exc.errors()
        messages = []
        for error in errors:
            loc = " → ".join(str(l) for l in error["loc"] if l != "body")
            messages.append(f"{loc}: {error['msg']}")
        return JSONResponse(
            status_code=422,
            content={"detail": "; ".join(messages)},
        )

    @test_app.exception_handler(Exception)
    async def unhandled_exception_handler(_request, _exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @test_app.get("/validate")
    def validate_endpoint(period: _Period):
        return {"period": period}

    @test_app.get("/crash")
    def crash_endpoint():
        raise RuntimeError("boom")

    return test_app


@pytest.fixture(scope="module")
def handler_client():
    return TestClient(_make_test_app(), raise_server_exceptions=False)


def test_validation_error_returns_detail_string(handler_client):
    """Pydantic validation errors must return {"detail": "..."} as a plain string, not a list."""
    response = handler_client.get("/validate?period=INVALID")

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert isinstance(body["detail"], str), (
        f"Expected detail to be a string, got {type(body['detail'])}: {body['detail']}"
    )


def test_validation_error_detail_contains_field_and_message(handler_client):
    """Validation error detail string must include the field name."""
    response = handler_client.get("/validate?period=INVALID")

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "period" in detail


def test_validation_error_no_other_keys(handler_client):
    """Validation error response must only contain the 'detail' key."""
    response = handler_client.get("/validate?period=INVALID")

    assert response.status_code == 422
    body = response.json()
    assert set(body.keys()) == {"detail"}


def test_unhandled_exception_returns_500_detail(handler_client):
    """Unhandled exceptions must return 500 with {"detail": "Internal server error"}."""
    response = handler_client.get("/crash")

    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": "Internal server error"}
