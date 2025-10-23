from sqlalchemy.orm import sessionmaker

from app.database.core import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
