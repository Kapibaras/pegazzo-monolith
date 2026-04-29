from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.balance import (
    BalanceMetricsDetailedQuerySchema,
    BalanceMetricsDetailedResponseSchema,
    BalanceMetricsQuerySchema,
    BalanceMetricsSimpleResponseSchema,
    BalanceTransactionsQuerySchema,
    BalanceTransactionsResponseSchema,
    BalanceTrendQuerySchema,
    BalanceTrendResponseSchema,
    TransactionAuthorizationSchema,
    TransactionCountQuerySchema,
    TransactionCountResponseSchema,
    TransactionPatchSchema,
    TransactionResponseSchema,
    TransactionSchema,
)
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
    # TODO: Accept car_id (optional) as body parameter once the car module is implemented.
    # Validate that car_id exists in the car table at that point.
    return service.create_transaction(data=body)


@router.delete(
    "/transaction/{reference}",
    response_model=ActionSuccess,
    status_code=status.HTTP_200_OK,
)
def delete_transaction(
    reference: str = Path(description="Transaction reference"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete a transaction."""
    service.delete_transaction(reference, user.role)
    return {"message": f"Transaction '{reference}' was successfully deleted."}


@router.patch("/transaction/{reference}", response_model=TransactionResponseSchema, status_code=status.HTTP_200_OK)
def update_transaction(
    reference: str = Path(description="Transaction reference"),
    body: TransactionPatchSchema = Body(..., description="Transaction data"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionResponseSchema:
    """Update a transaction."""
    # TODO: Accept car_id (optional) as body parameter once the car module is implemented.
    # Validate that car_id exists in the car table at that point.
    return service.update_transaction(reference, body, user.role)


@router.post(
    "/transaction/{reference}/authorization",
    response_model=TransactionResponseSchema,
    status_code=status.HTTP_200_OK,
)
def authorize_transaction(
    reference: str = Path(description="Transaction reference"),
    body: TransactionAuthorizationSchema = Body(..., description="New status"),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionResponseSchema:
    """Approve, reject or resubmit a transaction."""
    return service.authorize_transaction(reference, body.status, user.role)


@router.get(
    "/metrics",
    response_model=BalanceMetricsDetailedResponseSchema,
    status_code=status.HTTP_200_OK,
)
def get_management_metrics(
    params: BalanceMetricsDetailedQuerySchema = Depends(BalanceMetricsDetailedQuerySchema),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> BalanceMetricsDetailedResponseSchema:
    """Get detailed balance metrics for dashboard."""
    return service.get_management_metrics(
        period=params.period,
        week=params.week,
        month=params.month,
        year=params.year,
    )


@router.get("/metrics/simple", response_model=BalanceMetricsSimpleResponseSchema, status_code=status.HTTP_200_OK)
def get_metrics(
    params: BalanceMetricsQuerySchema = Depends(BalanceMetricsQuerySchema),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> BalanceMetricsSimpleResponseSchema:
    """Get metrics."""
    return service.get_metrics(month=params.month, year=params.year)


@router.get("/metrics/trend", response_model=BalanceTrendResponseSchema, status_code=status.HTTP_200_OK)
def get_trend(
    params: BalanceTrendQuerySchema = Depends(BalanceTrendQuerySchema),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER])),
) -> BalanceTrendResponseSchema:
    """Get historical balance data."""
    return service.get_historical(period=params.period, limit=params.limit)


@router.get(
    "/transactions/count",
    response_model=TransactionCountResponseSchema,
    status_code=status.HTTP_200_OK,
)
def get_transactions_count(
    params: TransactionCountQuerySchema = Depends(TransactionCountQuerySchema),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> TransactionCountResponseSchema:
    """Get count of transactions for a given month/year with an optional status filter."""
    return service.get_transactions_count(month=params.month, year=params.year, status=params.status)


@router.get("/transactions", response_model=BalanceTransactionsResponseSchema, status_code=status.HTTP_200_OK)
def get_balance_transactions(
    params: BalanceTransactionsQuerySchema = Depends(BalanceTransactionsQuerySchema),
    service: BalanceService = Depends(ServiceFactory.balance_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> BalanceTransactionsResponseSchema:
    """List transactions for a given period with pagination & sorting."""
    return service.get_transactions(
        period=params.period,
        week=params.week,
        month=params.month,
        year=params.year,
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        status=params.status,
    )
