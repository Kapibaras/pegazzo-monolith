from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.driver import (
    DriverCreateSchema,
    DriverDetailResponseSchema,
    DriverListQuerySchema,
    DriverListResponseSchema,
    DriverPatchSchema,
    DriverResponseSchema,
    DriverStatusSchema,
)
from app.schemas.user import ActionSuccess
from app.services.driver import DriverService

router = APIRouter(prefix="/management/drivers", tags=["Drivers"])


@router.get("", response_model=DriverListResponseSchema, status_code=status.HTTP_200_OK)
def list_drivers(
    params: Annotated[DriverListQuerySchema, Query()],
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
    "/{driver_id}/status",
    response_model=DriverResponseSchema,
    status_code=status.HTTP_200_OK,
)
def change_driver_status(
    driver_id: str = Path(..., description="Driver id"),
    body: DriverStatusSchema = Body(..., description="New driver status"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DriverResponseSchema:
    """Change a driver's operational status."""
    return service.change_driver_status(driver_id, body)


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


@router.patch(
    "/{driver_id}",
    response_model=DriverResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_driver(
    driver_id: str = Path(..., description="Driver id"),
    body: DriverPatchSchema = Body(..., description="Fields to update"),
    service: DriverService = Depends(ServiceFactory.driver_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DriverResponseSchema:
    """Update a driver's fields partially (excluding status)."""
    return service.update_driver(driver_id, body)


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
    """Delete an archived driver (soft delete when it has history, cascade delete otherwise)."""
    return service.delete_driver(driver_id)
