from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.balance import TransactionPatchSchema, TransactionResponseSchema, TransactionSchema
from app.schemas.user import ActionSuccess
from app.services.balance import BalanceService

router = APIRouter(prefix="/management/balance", tags=["Balance"])


@router.get(
    "/transaction/{reference}",
    response_model=TransactionResponseSchema,
    status_code=status.HTTP_200_OK,
)
def get_transaction(
    reference: str = Path(description="Transaction reference"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionResponseSchema:
    """Get a transaction by reference."""
    return service.get_transaction(reference)


@router.post(
    "/transaction",
    response_model=TransactionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    body: TransactionSchema = Body(..., description="Transaction data"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionResponseSchema:
    """Create a new transaction."""
    return service.create_transaction(data=body)


@router.delete(
    "/transaction/{reference}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_transaction(
    reference: str = Path(description="Transaction reference"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> ActionSuccess:
    """Delete a transaction."""
    service.delete_transaction(reference)
    return {"message": f"Transaction '{reference}' was successfully deleted."}


@router.patch("/transaction/{reference}", response_model=TransactionResponseSchema, status_code=status.HTTP_200_OK)
def update_transaction(
    reference: str = Path(description="Transaction reference"),
    body: TransactionPatchSchema = Body(..., description="Transaction data"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> TransactionResponseSchema:
    """Update a transaction."""
    return service.update_transaction(reference, body)
