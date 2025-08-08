from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi_jwt_auth.exceptions import AuthJWTException

from app.auth.role_checker import RoleChecker
from app.errors.auth import (
    ForbiddenRoleException,
    InvalidOrMissingToken,
    InvalidTokenException,
)


def test_role_checker_allows_valid_admin():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "admin_user", "role": "administrator"}

    checker = RoleChecker(["administrator"])
    sub, role = checker(authorize=mock_authorize)

    assert sub == "admin_user"
    assert role == "administrator"


def test_role_checker_rejects_invalid_token():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.side_effect = AuthJWTException("Invalid token")

    checker = RoleChecker(["administrator"])

    with pytest.raises(InvalidOrMissingToken):
        checker(authorize=mock_authorize)


def test_role_checker_missing_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user_without_role"}

    checker = RoleChecker(["administrator"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_missing_all_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {}

    checker = RoleChecker(["administrator"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_empty_username_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "", "role": "administrator"}

    checker = RoleChecker(["administrator"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


@pytest.mark.parametrize("bad_role", [None, ""])
def test_role_checker_invalid_role_value_raises(bad_role):
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user", "role": bad_role}

    checker = RoleChecker(["administrator"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_forbidden_role_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "normal_user", "role": "employee"}

    checker = RoleChecker(["administrator"])

    with pytest.raises(ForbiddenRoleException) as exc_info:
        checker(authorize=mock_authorize)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    expected_role = "employee"
    expected_allowed = ["administrator"]
    assert f"Role: {expected_role}" in exc_info.value.detail
    assert f"Allowed roles: {expected_allowed}" in exc_info.value.detail


def test_role_checker_valid_when_role_last_in_allowed_list():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "employee_user", "role": "employee"}

    checker = RoleChecker(["administrator", "employee"])

    sub, role = checker(authorize=mock_authorize)

    assert sub == "employee_user"
    assert role == "employee"
