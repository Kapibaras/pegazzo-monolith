from sqlalchemy.orm import Session

from app.database.session import SessionLocal


def get_db() -> Session:
    """Yield a database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
