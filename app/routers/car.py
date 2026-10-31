from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.car import (
    CarDetailResponseSchema,
    CarListQuerySchema,
    CarListResponseSchema,
    CarResponseSchema,
    CarSchema,
    CarStatusUpdateSchema,
    CarUpdateSchema,
)
from app.schemas.car_folio import CarFolioRequestSchema, CarFolioResponseSchema
from app.schemas.user import ActionSuccess
from app.services.car import CarService
from app.services.car_folio import CarFolioService

router = APIRouter(prefix="/management/cars", tags=["Cars"])


@router.get("", response_model=CarListResponseSchema, status_code=status.HTTP_200_OK)
def list_cars(
    params: CarListQuerySchema = Depends(CarListQuerySchema),
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> CarListResponseSchema:
    """List cars with optional filters, fuzzy search, sorting and pagination.

    - **search**: fuzzy match over make, model and id. A 4-digit token is treated as a year filter.
      Precedence: exact id > model > make. Plate is not searched.
    - **year**: exact year filter (e.g. 2022). Overrides any year token found in search.
    - **archived**: set to true to retrieve archived cars; defaults to false (active cars only).
    - **sort_by**: make, plate, status, year or created_at.
    - **sort_order**: asc or desc.
    """
    return service.list_cars(params)


@router.get("/{car_id}", response_model=CarDetailResponseSchema, status_code=status.HTTP_200_OK)
def get_car(
    car_id: str,
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> CarDetailResponseSchema:
    """Return the full detail for a car.

    Includes all car fields, insurance/policy, linked associate, documents with presigned GET URLs
    and computed expiry status, and the assigned driver from the active contract (if any).

    Returns 404 if the car does not exist.
    """
    return service.get_car(car_id)


@router.post(
    "/folio",
    response_model=CarFolioResponseSchema,
    status_code=status.HTTP_200_OK,
)
def compute_car_folio(
    body: CarFolioRequestSchema = Body(..., description="Inputs for folio computation"),
    service: CarFolioService = Depends(ServiceFactory.car_folio_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarFolioResponseSchema:
    """Compute the internal folio for a car without persisting anything.

    The folio encodes the owner prefix, associate initials, car model abbreviation,
    transmission and a per-associate consecutive counter.

    Returns 400 if the associate does not exist or the make/model pair is not
    registered in the CarModel catalog.
    """
    return service.compute_folio(data=body)


@router.post(
    "",
    response_model=CarResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_car(
    body: CarSchema = Body(..., description="Car data"),
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Register a new car."""
    return service.create_car(data=body)


@router.patch("/{car_id}", response_model=CarResponseSchema, status_code=status.HTTP_200_OK)
def update_car(
    car_id: str,
    body: CarUpdateSchema = Body(..., description="Fields to update; omitted fields are left unchanged"),
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Update a car partially (car data, insurance/policy, associate and image URLs).

    The status is changed through `PATCH /{car_id}/status`. Documents and the assigned driver are
    managed elsewhere. Changing `vin` or `plate` re-validates uniqueness (excluding the car itself).

    Returns 404 if the car does not exist; 400 if the vin/plate already exist, the policy expiration
    date is in the past, the insurance provider or associate do not exist, or the resulting financing
    data is incomplete; 422 if the body is empty or invalid.
    """
    return service.update_car(car_id, body)


@router.patch("/{car_id}/status", response_model=CarResponseSchema, status_code=status.HTTP_200_OK)
def update_car_status(
    car_id: str,
    body: CarStatusUpdateSchema = Body(..., description="New status"),
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Change the car status (ACTIVE, INACTIVE or IN_MAINTENANCE).

    Returns 404 if the car does not exist and 422 if the status is not a valid value.
    """
    return service.update_status(car_id, body.status)


@router.patch("/{car_id}/archive", response_model=CarResponseSchema, status_code=status.HTTP_200_OK)
def archive_car(
    car_id: str,
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Archive a car (sets `archived_at`).

    Returns 404 if the car does not exist and 400 if it is already archived or has an active
    assignment ("Cannot archive a car with an active assignment").
    """
    return service.archive_car(car_id)


@router.patch("/{car_id}/unarchive", response_model=CarResponseSchema, status_code=status.HTTP_200_OK)
def unarchive_car(
    car_id: str,
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Restore an archived car (clears `archived_at`).

    Returns 404 if the car does not exist and 400 if it is not archived.
    """
    return service.unarchive_car(car_id)


@router.delete("/{car_id}", response_model=ActionSuccess, status_code=status.HTTP_200_OK)
def delete_car(
    car_id: str,
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete an archived car.

    A car without history (contracts, transactions, events, incidences) is permanently deleted along
    with its exclusive documents, and its storage files are moved to the `deleted/` prefix. A car
    with history is soft-deleted: its data is kept but it disappears from every endpoint. Its VIN and
    plate stay reserved.

    Returns 404 if the car does not exist and 400 if it is not archived ("Car must be archived before deletion").
    """
    return service.delete_car(car_id)
