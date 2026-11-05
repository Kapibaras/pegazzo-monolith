from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.garage import GarageCreateSchema, GaragePatchSchema, GarageResponseSchema
from app.schemas.user import ActionSuccess
from app.services.garage import GarageService

router = APIRouter(prefix="/management", tags=["Drivers", "Garages"])


@router.post(
    "/drivers/{driver_id}/garages",
    response_model=GarageResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_garage(
    driver_id: str = Path(..., description="Driver id"),
    body: GarageCreateSchema = Body(..., description="Garage address"),
    service: GarageService = Depends(ServiceFactory.garage_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> GarageResponseSchema:
    """Create a garage for the driver. Its address proof is uploaded as a `proof_of_address` document of the garage."""
    return service.create_garage(driver_id=driver_id, data=body)


@router.patch(
    "/drivers/{driver_id}/garages/{garage_id}",
    response_model=GarageResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_garage(
    driver_id: str = Path(..., description="Driver id"),
    garage_id: int = Path(..., description="Garage id"),
    body: GaragePatchSchema = Body(..., description="New address"),
    service: GarageService = Depends(ServiceFactory.garage_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> GarageResponseSchema:
    """Replace the address of a garage of the driver."""
    return service.update_garage(driver_id=driver_id, garage_id=garage_id, data=body)


@router.delete(
    "/drivers/{driver_id}/garages/{garage_id}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_garage(
    driver_id: str = Path(..., description="Driver id"),
    garage_id: int = Path(..., description="Garage id"),
    service: GarageService = Depends(ServiceFactory.garage_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete a garage of the driver together with its documents."""
    service.delete_garage(driver_id=driver_id, garage_id=garage_id)
    return {"message": "Garage removed successfully"}
