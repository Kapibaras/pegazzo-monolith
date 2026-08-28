from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

import app.auth.core
import app.database.events
from app.config import CORS_ORIGINS, DEBUG, ENVIRONMENT, AppConfig
from app.database.core import test_connection
from app.routers import (
    associate_router,
    auth_router,
    balance_router,
    car_model_router,
    car_router,
    document_router,
    health_router,
    image_router,
    insurance_router,
    user_router,
)

app = FastAPI(
    debug=DEBUG,
    title=AppConfig.NAME,
    description=AppConfig.DESCRIPTION,
    version=AppConfig.VERSION,
)


if ENVIRONMENT != "LOCAL":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# * EXCEPTION HANDLERS * #


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    """Normalize Pydantic validation errors to { "detail": "..." }."""
    errors = exc.errors()
    messages = []
    for error in errors:
        loc = " → ".join(str(l) for l in error["loc"] if l != "body")
        messages.append(f"{loc}: {error['msg']}")
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(messages)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, _exc: Exception):
    """Catch-all: guarantee { "detail": "..." } for unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
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

app.include_router(health_router)
app.include_router(auth_router, prefix="/pegazzo")
app.include_router(user_router, prefix="/pegazzo")
app.include_router(balance_router, prefix="/pegazzo")
app.include_router(insurance_router, prefix="/pegazzo")
app.include_router(associate_router, prefix="/pegazzo")
app.include_router(car_model_router, prefix="/pegazzo")
app.include_router(car_router, prefix="/pegazzo")
app.include_router(document_router, prefix="/pegazzo")
app.include_router(image_router, prefix="/pegazzo")

# * HANDLERS * #

handler = Mangum(app)
