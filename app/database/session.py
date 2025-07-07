from sqlalchemy.orm import sessionmaker, scoped_session
from app.database.core import engine

SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))
