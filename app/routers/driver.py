from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.driver import (
    DriverCreateSchema,
    DriverDetailResponseSchema,
    DriverListQuerySchema,
    DriverListResponseSchema,
    DriverResponseSchema,
)
from app.schemas.user import ActionSuccess
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


@router.get("/{driver_id}", response_model=DriverDetailResponseSchema, status_code=status.HTTP_200_OK)
def get_driver(
    driver_id: str,
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> DriverDetailResponseSchema:
    """Return the full detail for a single driver."""
    return service.get_driver(driver_id)


@router.patch(
    "/{driver_id}/archive",
    response_model=DriverResponseSchema,
    status_code=status.HTTP_200_OK,
)
def archive_driver(
    driver_id: str = Path(..., description="Driver id"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DriverResponseSchema:
    """Archive a driver by setting archived_at."""
    return service.archive_driver(driver_id)


@router.patch(
    "/{driver_id}/unarchive",
    response_model=DriverResponseSchema,
    status_code=status.HTTP_200_OK,
)
def unarchive_driver(
    driver_id: str = Path(..., description="Driver id"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DriverResponseSchema:
    """Restore an archived driver."""
    return service.unarchive_driver(driver_id)


@router.delete(
    "/{driver_id}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_driver(
    driver_id: str = Path(..., description="Driver id"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Permanently delete an archived driver with cascade cleanup."""
    service.delete_driver(driver_id)
    return {"message": "Driver deleted successfully"}
