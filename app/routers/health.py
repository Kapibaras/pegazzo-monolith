from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database.core import test_connection

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint. Verifies the API and database are operational."""
    try:
        test_connection()
    except RuntimeError:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}
