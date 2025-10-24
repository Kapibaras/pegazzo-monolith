from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.auth import AuthUser, RequiresAuth, Role
from app.dependencies import ServiceFactory
from app.schemas.user import (
    ActionSuccess,
    UserCreateSchema,
    UserSchema,
    UserUpdateNameSchema,
    UserUpdatePasswordSchema,
    UserUpdateRoleSchema,
)
from app.services import UserService

router = APIRouter(prefix="/internal/user", tags=["User"])


@router.get("", response_model=list[UserSchema])
def get_all_users(
    service: UserService = Depends(ServiceFactory.user_service),
    role: Role = Query(None, description="Filter by user role"),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> list[UserSchema]:
    """Get all users, optionally filtered by role name."""
    return service.get_all_users(role)


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateSchema = Body(..., description="User data to create"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> UserSchema:
    """Create a new user."""
    return service.create_user(data=body)


@router.get("/{username}", response_model=UserSchema)
def get_user(
    username: str = Path(description="Username of the user"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth()),
) -> UserSchema:
    """Get a user by username."""
    return service.get_user(username)


@router.delete("/{username}", response_model=ActionSuccess)
def delete_user(
    username: str = Path(description="Username of the user"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> ActionSuccess:
    """Delete a user by username."""
    service.delete_user(username)
    return {"message": f"User '{username}' was successfully deleted."}


@router.patch("/{username}/name", response_model=ActionSuccess)
def update_user_name(
    username: str = Path(description="Username of the user"),
    body: UserUpdateNameSchema = Body(..., description="User data to update"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> UserSchema:
    """Update a user by username."""
    service.update_user_name(username, body)
    return {"message": f"User '{username}' name was successfully updated."}


@router.patch("/{username}/role", response_model=ActionSuccess)
def update_user_role(
    username: str = Path(description="Username of the user"),
    body: UserUpdateRoleSchema = Body(..., description="User data to update"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> UserSchema:
    """Update a user by username."""
    service.update_user_role(username, body)
    return {"message": f"User '{username}' role was successfully updated."}


@router.patch("/{username}/password", response_model=ActionSuccess)
def update_user_password(
    username: str = Path(description="Username of the user"),
    body: UserUpdatePasswordSchema = Body(..., description="New password data"),
    service: UserService = Depends(ServiceFactory.user_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> UserSchema:
    """Update a user password by username."""
    service.update_user_password(username, body)
    return {"message": f"User '{username}' password was successfully updated."}
