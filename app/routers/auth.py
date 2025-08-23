from fastapi import APIRouter, Body, Depends

from app.auth.role_checker import RoleChecker
from app.dependencies import ServiceFactory
from app.schemas.user import ActionSuccess, PermissionsResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/internal/auth", tags=["Auth"])


@router.get("/permissions", response_model=PermissionsResponse)
def permissions(
    service: AuthService = Depends(ServiceFactory.auth_service),
    user=Depends(RoleChecker()),
) -> PermissionsResponse:
    """Get the current user's permissions."""
    return service.get_permissions()


@router.post("/login", response_model=ActionSuccess)
def login(
    username: str = Body(..., description="Username for login"),
    password: str = Body(..., description="Password for login"),
    service: AuthService = Depends(ServiceFactory.auth_service),
) -> ActionSuccess:
    """Login a user and return an action success response."""
    service.login(username, password)
    return {"message": "Successful login"}


@router.post("/refresh", response_model=ActionSuccess)
def refresh(service: AuthService = Depends(ServiceFactory.auth_service)) -> ActionSuccess:
    """Refresh a user's access token and return an action success response."""
    service.refresh()
    return {"message": "Token refreshed successfully"}


@router.post("/logout", response_model=ActionSuccess)
def logout(service: AuthService = Depends(ServiceFactory.auth_service)) -> ActionSuccess:
    """Logout a user and return an action success response."""
    service.logout()
    return {"message": "Successful logout"}
