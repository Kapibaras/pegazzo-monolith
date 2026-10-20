import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database.core import test_connection

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_broker() -> str:
    """Ping the Celery broker. Returns 'ok' or 'unreachable'."""
    try:
        from app.worker.celery_app import app as celery_app

        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=3)
        conn.close()
    except Exception:
        logger.warning("Broker health check failed", exc_info=True)
        return "unreachable"
    else:
        return "ok"


@router.get("/health")
async def health():
    """Health check endpoint. Verifies the API, database, and broker are operational."""
    try:
        test_connection()
    except RuntimeError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable", "broker": "unknown"},
        )

    broker_status = _check_broker()

    return {"status": "ok", "database": "ok", "broker": broker_status}
