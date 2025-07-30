from sqlalchemy.orm import scoped_session, sessionmaker

from app.database.core import engine

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
