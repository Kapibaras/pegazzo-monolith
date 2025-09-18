from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class Document(Base):
    """Document entity - stores all documents."""

    __tablename__ = "document"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
