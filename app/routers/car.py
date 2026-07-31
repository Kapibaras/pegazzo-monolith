from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.car import CarDetailResponseSchema, CarListQuerySchema, CarListResponseSchema, CarResponseSchema, CarSchema
from app.services.car import CarService

router = APIRouter(prefix="/management/cars", tags=["Cars"])


@router.get("", response_model=CarListResponseSchema, status_code=status.HTTP_200_OK)
def list_cars(
    params: CarListQuerySchema = Depends(CarListQuerySchema),
    service: CarService = Depends(ServiceFactory.car_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> CarListResponseSchema:
    """List cars with optional filters (status, search, archived), sorting and pagination.

    - **search**: matches plate, make or model (case-insensitive).
    - **archived**: set to true to retrieve archived cars; defaults to false (active cars only).
    - **sort_by**: make, plate, status or created_at.
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
