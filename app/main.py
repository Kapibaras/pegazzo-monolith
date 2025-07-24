from fastapi import FastAPI
from mangum import Mangum
from app.config import AppConfig, DEBUG
from app.database import get_db
from app.database.core import test_connection
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(
    debug=DEBUG,
    title=AppConfig.NAME,
    description=AppConfig.DESCRIPTION,
    version=AppConfig.VERSION
)


@app.get("/")
def root(db: Session = Depends(get_db)):
    return {"message": "Bienvenido a la API de Pegazzo Drivers"}


@app.on_event("startup")
def on_startup():
    test_connection()


handler = Mangum(app)
