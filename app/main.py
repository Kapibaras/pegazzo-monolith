from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

import app.auth.core
from app.config import DEBUG, ENVIRONMENT, AppConfig
from app.database.core import test_connection
from app.routers import auth_router, user_router

app = FastAPI(
    debug=DEBUG,
    title=AppConfig.NAME,
    description=AppConfig.DESCRIPTION,
    version=AppConfig.VERSION,
)


if ENVIRONMENT == "LOCAL":
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
