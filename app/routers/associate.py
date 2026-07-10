from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.associate import AssociatePatchSchema, AssociateResponseSchema, AssociateSchema
from app.schemas.user import ActionSuccess
from app.services.associate import AssociateService

router = APIRouter(prefix="/management/associates", tags=["Associates"])


@router.post(
    "",
    response_model=AssociateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_associate(
    body: AssociateSchema = Body(..., description="Associate data"),
    service: AssociateService = Depends(ServiceFactory.associate_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> AssociateResponseSchema:
    """Create a new associate."""
    return service.create(data=body)


@router.get(
    "",
    response_model=list[AssociateResponseSchema],
    status_code=status.HTTP_200_OK,
)
def list_associates(
    search: Optional[str] = Query(default=None, description="Filter by name or surnames"),
    service: AssociateService = Depends(ServiceFactory.associate_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> list[AssociateResponseSchema]:
    """List all associates."""
    return service.list_all(search=search)


@router.patch(
    "/{associate_id}",
    response_model=AssociateResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_associate(
    associate_id: int = Path(..., description="Associate id"),
    body: AssociatePatchSchema = Body(..., description="Fields to update"),
    service: AssociateService = Depends(ServiceFactory.associate_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> AssociateResponseSchema:
    """Update an associate."""
    return service.update(associate_id=associate_id, data=body)


@router.delete(
    "/{associate_id}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_associate(
    associate_id: int = Path(..., description="Associate id"),
    service: AssociateService = Depends(ServiceFactory.associate_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete an associate. Blocked if linked to cars."""
    service.delete(associate_id=associate_id)
    return {"message": "Associate deleted successfully"}
