from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base

from app.config import DATABASE_URL, DEBUG

engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

Base = declarative_base()


def test_connection():
    """Test the database connection."""

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        message = f"❌ Error when connecting to the database: {e}"
        raise RuntimeError(message) from e
