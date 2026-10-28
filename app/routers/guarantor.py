from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.guarantor import GuarantorCreateSchema, GuarantorPatchSchema, GuarantorResponseSchema
from app.schemas.user import ActionSuccess
from app.services.guarantor import GuarantorService

router = APIRouter(prefix="/management", tags=["Drivers", "Guarantors"])


@router.post(
    "/drivers/{driver_id}/guarantors",
    response_model=GuarantorResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_guarantor(
    driver_id: str = Path(..., description="Driver id"),
    body: GuarantorCreateSchema = Body(..., description="Guarantor data"),
    service: GuarantorService = Depends(ServiceFactory.guarantor_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> GuarantorResponseSchema:
    """Create a new guarantor and link it to the driver."""
    return service.create_guarantor(driver_id=driver_id, data=body)


@router.patch(
    "/guarantors/{guarantor_id}",
    response_model=GuarantorResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_guarantor(
    guarantor_id: int = Path(..., description="Guarantor id"),
    body: GuarantorPatchSchema = Body(..., description="Fields to update"),
    service: GuarantorService = Depends(ServiceFactory.guarantor_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> GuarantorResponseSchema:
    """Update a guarantor."""
    return service.update_guarantor(guarantor_id=guarantor_id, data=body)


@router.delete(
    "/drivers/{driver_id}/guarantors/{guarantor_id}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_guarantor(
    driver_id: str = Path(..., description="Driver id"),
    guarantor_id: int = Path(..., description="Guarantor id"),
    service: GuarantorService = Depends(ServiceFactory.guarantor_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Unlink a guarantor from a driver. Deletes the guarantor if it has no other linked drivers."""
    service.delete_guarantor(driver_id=driver_id, guarantor_id=guarantor_id)
    return {"message": "Guarantor removed successfully"}
