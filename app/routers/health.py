import asyncio
import contextlib
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database.core import test_connection

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_broker_sync() -> str:
    """Ping the Celery broker (blocking). Returns 'ok' or 'unreachable'."""
    conn = None
    try:
        from app.worker.celery_app import app as celery_app

        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=3)
    except Exception:
        logger.warning("Broker health check failed", exc_info=True)
        return "unreachable"
    else:
        return "ok"
    finally:
        if conn is not None:
            with contextlib.suppress(ConnectionError, OSError):
                conn.close()


def _check_db_sync() -> str:
    """Test the database connection (blocking). Returns 'ok' or 'unreachable'."""
    try:
        test_connection()
    except RuntimeError:
        return "unreachable"
    return "ok"


async def _check_broker() -> str:
    """Run the blocking broker check in a thread to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _check_broker_sync)


async def _check_db() -> str:
    """Run the blocking DB check in a thread to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _check_db_sync)


@router.get("/health")
async def health():
    """Health check endpoint. Verifies the API, database, and broker are operational."""
    db_status, broker_status = await asyncio.gather(_check_db(), _check_broker())

    if db_status != "ok":
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": db_status, "broker": broker_status},
        )

    status = "degraded" if broker_status != "ok" else "ok"
    return {"status": status, "database": db_status, "broker": broker_status}
