from fastapi import FastAPI
from mangum import Mangum

from app.config import DEBUG, AppConfig
from app.database.core import test_connection
from app.routers import auth_router, user_router

app = FastAPI(
    debug=DEBUG,
    title=AppConfig.NAME,
    description=AppConfig.DESCRIPTION,
    version=AppConfig.VERSION,
)


@app.get("/", tags=["Root"])
def root():
    """Root endpoint."""
    return {"message": "Bienvenido a la API de Pegazzo Drivers"}


@app.on_event("startup")
def on_startup():
    """Startup event handler."""
    test_connection()


# * ROUTERS * #

app.include_router(auth_router, prefix="/pegazzo")
app.include_router(user_router, prefix="/pegazzo")

# * HANDLERS * #

handler = Mangum(app)
