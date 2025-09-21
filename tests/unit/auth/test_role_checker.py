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


def test_role_checker_allows_valid_owner():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "owner_user", "role": "propietario"}

    checker = RoleChecker(["propietario"])
    sub, role = checker(authorize=mock_authorize)

    assert sub == "owner_user"
    assert role == "propietario"


def test_role_checker_rejects_invalid_token():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.side_effect = AuthJWTException("Invalid token")

    checker = RoleChecker(["propietario"])

    with pytest.raises(InvalidOrMissingToken):
        checker(authorize=mock_authorize)


def test_role_checker_missing_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user_without_role"}

    checker = RoleChecker(["propietario"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_missing_all_claims_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {}

    checker = RoleChecker(["propietario"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_empty_username_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "", "role": "propietario"}

    checker = RoleChecker(["propietario"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


@pytest.mark.parametrize("bad_role", [None, ""])
def test_role_checker_invalid_role_value_raises(bad_role):
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "user", "role": bad_role}

    checker = RoleChecker(["propietario"])

    with pytest.raises(InvalidTokenException):
        checker(authorize=mock_authorize)


def test_role_checker_forbidden_role_raises():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "normal_user", "role": "empleado"}

    checker = RoleChecker(["propietario"])

    with pytest.raises(ForbiddenRoleException) as exc_info:
        checker(authorize=mock_authorize)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    expected_role = "empleado"
    expected_allowed = ["propietario"]
    assert f"Role: {expected_role}" in exc_info.value.detail
    assert f"Allowed roles: {expected_allowed}" in exc_info.value.detail


def test_role_checker_valid_when_role_last_in_allowed_list():
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "empleado_user", "role": "empleado"}

    checker = RoleChecker(["propietario", "administrador", "empleado"])

    sub, role = checker(authorize=mock_authorize)

    assert sub == "empleado_user"
    assert role == "empleado"


def test_role_checker_allows_any_role_when_no_allowed_roles_defined():
    """Test that any role is allowed when no allowed roles are defined."""
    mock_authorize = MagicMock()
    mock_authorize.jwt_required.return_value = None
    mock_authorize.get_raw_jwt.return_value = {"sub": "any_user", "role": "random_role"}

    checker = RoleChecker([])

    sub, role = checker(authorize=mock_authorize)

    assert sub == "any_user"
    assert role == "random_role"
