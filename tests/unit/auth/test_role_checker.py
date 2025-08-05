from unittest.mock import MagicMock

import pytest
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
    mock_authorize.get_raw_jwt.return_value = {"sub": "admin_user", "role": "admin"}

    checker = RoleChecker(["admin"])
    sub, role = checker(authorize=mock_authorize)

    assert sub == "admin_user"
    assert role == "admin"


def test_role_checker_rejects_invalid_token():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.side_effect = AuthJWTException("Invalid token")

    checker = RoleChecker(["admin"])

    with pytest.raises(InvalidOrMissingToken):
        checker(authorize=mock_authorize)


def test_role_checker_missing_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user_without_role"}

    checker = RoleChecker(["admin"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_missing_all_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {}

    checker = RoleChecker(["admin"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_empty_username_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "", "role": "admin"}

    checker = RoleChecker(["admin"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


@pytest.mark.parametrize("bad_role", [None, ""])
def test_role_checker_invalid_role_value_raises(bad_role):
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user", "role": bad_role}

    checker = RoleChecker(["admin"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_forbidden_role_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "normal_user", "role": "user"}

    checker = RoleChecker(["admin"])

    with pytest.raises(ForbiddenRoleException):
        checker(authorize=mock_authorize)


def test_role_checker_valid_when_role_last_in_allowed_list():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "moderator_user", "role": "moderator"}

    checker = RoleChecker(["user", "editor", "moderator"])

    sub, role = checker(authorize=mock_authorize)

    assert sub == "moderator_user"
    assert role == "moderator"
