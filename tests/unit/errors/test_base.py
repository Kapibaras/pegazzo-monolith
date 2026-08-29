from fastapi import HTTPException

from app.errors import PegazzoException


def test_pegazzo_exception_is_http_exception():
    exc = PegazzoException(status_code=400, detail="test error")
    assert isinstance(exc, HTTPException)


def test_pegazzo_exception_has_status_and_detail():
    exc = PegazzoException(status_code=404, detail="not found")
    assert exc.status_code == 404
    assert exc.detail == "not found"
