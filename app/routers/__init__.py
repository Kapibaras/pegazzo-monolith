from .associate import router as associate_router
from .auth import router as auth_router
from .balance import router as balance_router
from .health import router as health_router
from .insurance import router as insurance_router
from .user import router as user_router

__all__ = ["associate_router", "auth_router", "balance_router", "health_router", "insurance_router", "user_router"]
