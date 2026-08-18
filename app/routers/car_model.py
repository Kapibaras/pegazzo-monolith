from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.car_model import CarModelCreateSchema, CarModelGroupSchema, CarModelResponseSchema
from app.services.car_model import CarModelService

router = APIRouter(prefix="/management/cars/models", tags=["Car Models"])


@router.get("", response_model=list[CarModelGroupSchema], status_code=status.HTTP_200_OK)
def list_car_models(
    service: CarModelService = Depends(ServiceFactory.car_model_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> list[CarModelGroupSchema]:
    """Return the full car model catalog grouped by make.

    Used by the car registration wizard combobox and by the folio computation endpoint.
    """
    return service.list_grouped()


@router.post("", response_model=CarModelResponseSchema, status_code=status.HTTP_201_CREATED)
def create_car_model(
    body: CarModelCreateSchema = Body(..., description="Car model catalog entry to create"),
    service: CarModelService = Depends(ServiceFactory.car_model_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> CarModelResponseSchema:
    """Add a new (make, model, abbreviation) entry to the catalog.

    Returns 400 if the (make, model) pair already exists.
    """
    return service.create(data=body)


@router.delete("/{car_model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car_model(
    car_model_id: int,
    service: CarModelService = Depends(ServiceFactory.car_model_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> None:
    """Delete a catalog entry by id.

    Returns 404 if the entry does not exist.
    """
    service.delete(car_model_id)
