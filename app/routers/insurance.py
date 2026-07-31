
from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.insurance import InsurancePatchSchema, InsuranceResponseSchema, InsuranceSchema
from app.schemas.user import ActionSuccess
from app.services.insurance import InsuranceService

router = APIRouter(prefix="/management/cars/insurance", tags=["Cars", "Insurance"])


@router.post(
    "",
    response_model=InsuranceResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_insurance(
    body: InsuranceSchema = Body(..., description="Insurance provider data"),
    service: InsuranceService = Depends(ServiceFactory.insurance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> InsuranceResponseSchema:
    """Create a new insurance provider."""
    return service.create(data=body)


@router.get(
    "",
    response_model=list[InsuranceResponseSchema],
    status_code=status.HTTP_200_OK,
)
def list_insurances(
    search: str | None = Query(default=None, description="Filter by name"),
    service: InsuranceService = Depends(ServiceFactory.insurance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> list[InsuranceResponseSchema]:
    """List all insurance providers."""
    return service.list_all(search=search)


@router.patch(
    "/{insurance_id}",
    response_model=InsuranceResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_insurance(
    insurance_id: int = Path(..., description="Insurance provider id"),
    body: InsurancePatchSchema = Body(..., description="Fields to update"),
    service: InsuranceService = Depends(ServiceFactory.insurance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> InsuranceResponseSchema:
    """Update an insurance provider."""
    return service.update(insurance_id=insurance_id, data=body)


@router.delete(
    "/{insurance_id}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_insurance(
    insurance_id: int = Path(..., description="Insurance provider id"),
    service: InsuranceService = Depends(ServiceFactory.insurance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete an insurance provider. Blocked if referenced by any car."""
    service.delete(insurance_id=insurance_id)
    return {"message": "Insurance provider deleted successfully"}
