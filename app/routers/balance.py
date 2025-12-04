from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.balance import TransactionResponseSchema, TransactionSchema
from app.services.balance import BalanceService

router = APIRouter(prefix="/management/balance", tags=["Balance"])


@router.post("/transaction", response_model=TransactionResponseSchema, status_code=status.HTTP_201_CREATED)
def transaction(
    body: TransactionSchema = Body(..., description="Transaction data"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionResponseSchema:
    """Create a new transaction."""
    return service.create_transaction(data=body)
