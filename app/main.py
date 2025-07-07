from fastapi import FastAPI
from mangum import Mangum
from app.config import variables, constants
from app.database import Base, engine, get_db
from app.database.core import test_connection
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(
    debug=variables.DEBUG,
    title=constants.AppConfig.NAME,
    description=constants.AppConfig.DESCRIPTION,
    version=constants.AppConfig.VERSION
)


def create_all_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    test_connection()
    create_all_tables()


@app.get("/")
def root(db: Session = Depends(get_db)):
    return {"message": "Bienvenido a la API de Pegazzo Drivers"}


handler = Mangum(app)
