from fastapi import Depends, FastAPI
from mangum import Mangum
from sqlalchemy.orm import Session

from app.config import DEBUG, AppConfig
from app.database import get_db
from app.database.core import test_connection
from app.routers import user_router

app = FastAPI(
    debug=DEBUG,
    title=AppConfig.NAME,
    description=AppConfig.DESCRIPTION,
    version=AppConfig.VERSION,
)


@app.get("/", tags=["Root"])
def root(db: Session = Depends(get_db)):
    return {"message": "Bienvenido a la API de Pegazzo Drivers"}


@app.on_event("startup")
def on_startup():
    test_connection()


# * ROUTERS * #

app.include_router(user_router)

# * HANDLERS * #

handler = Mangum(app)
