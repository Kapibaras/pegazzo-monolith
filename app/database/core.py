from sqlalchemy import create_engine, text
from app.config import variables

DATABASE_URL = variables.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=variables.DEBUG,
    connect_args={
        "check_same_thread": False
    } if DATABASE_URL.startswith("sqlite") else {}
)


def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError("❌ Error al conectar a la base de datos") from e
