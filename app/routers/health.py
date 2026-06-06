from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint. Returns:dict: Status of the application."""
    return {"status": "ok"}
