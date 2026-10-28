from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database.base import Base


class Document(Base):
    """Document entity - stores all documents.

    Analysis status machine::

        not_analyzed → pending → processing → valid | review | rejected | failed
        review → accepted | rejected
        valid | accepted | rejected → superseded  (replaced by a newer document)

    Transitions are enforced by the analysis service (PGZ-124).
    """

    __tablename__ = "document"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String(40), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(50), nullable=False, default="UNCLASSIFIED")
    confidence = Column(Numeric(5, 4), nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    # Analysis pipeline columns
    status = Column(String(20), nullable=False, default="not_analyzed")
    detected_type = Column(String(40), nullable=True)
    review_reasons = Column(JSON, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    model_version = Column(String(50), nullable=True)
    error_reason = Column(String(50), nullable=True)

    # Human-verification traceability
    verified_by = Column(String(30), ForeignKey("user.username"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
