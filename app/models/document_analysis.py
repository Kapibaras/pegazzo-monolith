import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Uuid
from sqlalchemy.sql import func

from app.database.base import Base
from app.enum.document import AnalysisStatus


class DocumentAnalysis(Base):
    """Temporary analysis of uploaded files, before the entity they belong to exists (PGZ-179).

    Files live under ``private/tmp/analysis/{id}/{index}.{ext}`` until a section endpoint promotes the analysis to
    final ``Document`` rows (``status = consumed``). Status machine::

        uploaded → analyzed | rejected | failed → consumed
        uploaded → consumed  (evidence-only types)

    The result columns are filled by the analysis endpoint (PGZ-124). Not consumed rows older than 24 hours are removed
    by the cleanup task.
    """

    __tablename__ = "document_analysis"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    declared_type = Column(String(40), nullable=False)
    # [{"key": "tmp/analysis/{id}/0.jpg", "content_type": "image/jpeg", "size": 2400000}, ...]
    files = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default=AnalysisStatus.UPLOADED.value)
    reason = Column(String(50), nullable=True)

    # Analysis result (PGZ-124)
    detected_type = Column(String(40), nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    prefill = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(10, 6), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    created_by = Column(String(30), ForeignKey("user.username"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_document_analysis_status_created_at", "status", "created_at"),)
