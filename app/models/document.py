from sqlalchemy import JSON, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database.base import Base


class Document(Base):
    """Document entity - stores all documents."""

    __tablename__ = "document"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
