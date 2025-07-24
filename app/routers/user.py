from fastapi import APIRouter, Body, Depends, Path

from app.dependencies import ServiceFactory
from app.schemas.user import UserCreateSchema, UserSchema
from app.services import UserService

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/all")
def get_all_users(
    service: UserService = Depends(ServiceFactory.user_service),
) -> list[UserSchema]:
    return service.get_all_users()


@router.post("")
def create_user(
    body: UserCreateSchema = Body(..., description="User data to create"),
    service: UserService = Depends(ServiceFactory.user_service),
) -> UserSchema:
    return service.create_user(
        body.username, body.name, body.surnames, body.password, body.role_id
    )


@router.get("/{username}")
def get_user(
    username: str = Path(description="Username of the user"),
    service: UserService = Depends(ServiceFactory.user_service),
) -> UserSchema:
    return service.get_user(username)
