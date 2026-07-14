from .associate import router as associate_router
from .auth import router as auth_router
from .balance import router as balance_router
from .car import router as car_router
from .document import router as document_router
from .health import router as health_router
from .insurance import router as insurance_router
from .user import router as user_router

__all__ = ["associate_router", "auth_router", "balance_router", "car_router", "document_router", "health_router", "insurance_router", "user_router"]
