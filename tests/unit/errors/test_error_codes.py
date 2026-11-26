import asyncio
import json

from app.errors import PegazzoException
from app.main import pegazzo_exception_handler


def _render(exc: PegazzoException):
    response = asyncio.run(pegazzo_exception_handler(None, exc))
    return response.status_code, json.loads(response.body), response.headers


def test_error_without_code_keeps_detail_only_shape():
    status_code, body, _ = _render(PegazzoException(status_code=404, detail="Not here"))

    assert status_code == 404
    assert body == {"detail": "Not here"}


def test_error_with_code_includes_code():
    status_code, body, _ = _render(PegazzoException(status_code=400, detail="Too big", code="file_too_large"))

    assert status_code == 400
    assert body == {"detail": "Too big", "code": "file_too_large"}


def test_error_headers_are_preserved():
    _, _, headers = _render(PegazzoException(status_code=401, detail="Auth", headers={"WWW-Authenticate": "Basic"}))

    assert headers["www-authenticate"] == "Basic"
