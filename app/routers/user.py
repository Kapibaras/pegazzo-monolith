from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.auth.role_checker import RoleChecker
from app.dependencies import ServiceFactory
from app.schemas.user import ActionSuccess, RoleEnum, UserCreateSchema, UserSchema, UserUpdatePasswordSchema, UserUpdateSchema
from app.services import UserService

router = APIRouter(prefix="/internal/user", tags=["User"])


@router.get("", response_model=list[UserSchema])
def get_all_users(
    role: RoleEnum = Query(None, description="Filter by user role"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> list[UserSchema]:
    """Get all users, optionally filtered by role name."""
    return service.get_all_users(role)


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateSchema = Body(..., description="User data to create"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> UserSchema:
    """Create a new user."""
    return service.create_user(data=body)


@router.get("/{username}", response_model=UserSchema)
def get_user(
    username: str = Path(description="Username of the user"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> UserSchema:
    """Get a user by username."""
    return service.get_user(username)


@router.put("/{username}", response_model=UserSchema)
def update_user(
    username: str = Path(description="Username of the user"),
    body: UserUpdateSchema = Body(..., description="User data to update"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> UserSchema:
    """Update a user by username."""
    return service.update_user(username, body)


@router.delete("/{username}", response_model=ActionSuccess)
def delete_user(
    username: str = Path(description="Username of the user"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> ActionSuccess:
    """Delete a user by username."""
    service.delete_user(username)
    return {"message": f"User '{username}' was successfully deleted."}


@router.patch("/{username}/password", response_model=UserSchema)
def update_user_password(
    username: str = Path(description="Username of the user"),
    body: UserUpdatePasswordSchema = Body(..., description="New password data"),
    service: UserService = Depends(ServiceFactory.user_service),
    user=Depends(RoleChecker(["propietario"])),
) -> UserSchema:
    """Update a user password by username."""
    return service.update_user_password(username, body)
