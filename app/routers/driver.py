from fastapi import APIRouter, Depends

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.driver import DriverListQuerySchema, DriverListResponseSchema
from app.services.driver import DriverService

router = APIRouter(prefix="/management/drivers", tags=["Drivers"])


@router.get("", response_model=DriverListResponseSchema)
def list_drivers(
    params: DriverListQuerySchema = Depends(DriverListQuerySchema),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> DriverListResponseSchema:
    """Return a paginated, filtered and sorted list of drivers."""
    return service.list_drivers(params)
