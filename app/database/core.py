from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base

from app.config import DATABASE_URL, DEBUG

engine = create_engine(
    DATABASE_URL, echo=DEBUG, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

Base = declarative_base()


def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError("❌ Error al conectar a la base de datos") from e
