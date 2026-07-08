from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.car import CarResponseSchema, CarSchema
from app.services.car import CarService

router = APIRouter(prefix="/management/cars", tags=["Cars"])


@router.post(
    "",
    response_model=CarResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_car(
    body: CarSchema = Body(..., description="Car data"),
    service: CarService = Depends(ServiceFactory.car_service),
    # _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> CarResponseSchema:
    """Register a new car."""
    return service.create_car(data=body)
