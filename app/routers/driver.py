from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.driver import DriverCreateSchema, DriverListQuerySchema, DriverListResponseSchema, DriverResponseSchema
from app.services.driver import DriverService

router = APIRouter(prefix="/management/drivers", tags=["Drivers"])


@router.get("", response_model=DriverListResponseSchema, status_code=status.HTTP_200_OK)
def list_drivers(
    params: DriverListQuerySchema = Depends(DriverListQuerySchema),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> DriverListResponseSchema:
    """Return a paginated, filtered and sorted list of drivers."""
    return service.list_drivers(params)


@router.post(
    "",
    response_model=DriverResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_driver(
    body: DriverCreateSchema = Body(..., description="Driver data"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DriverResponseSchema:
    """Register a new driver."""
    return service.create_driver(data=body)
