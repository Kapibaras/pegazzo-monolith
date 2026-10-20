# TODO PGZ-124: Document analysis task
#
# This task will be the first real consumer of the Celery infrastructure.
# It downloads the document from R2, sends it to Gemini (via PGZ-164's
# extraction service), and writes the result back to the Document record.
#
# Proposed model for tracking analysis state (option B from PGZ-159 spike):
#
#   class AnalysisRequest(Base):
#       __tablename__ = "analysis_request"
#
#       id = Column(Integer, primary_key=True)
#       document_id = Column(Integer, ForeignKey("document.id"), nullable=False)
#       task_id = Column(String(255), nullable=True)    # Celery task ID
#       status = Column(String(20), nullable=False)      # processing, valid, review, rejected, failed
#       failure_reason = Column(String(50), nullable=True)  # stuck, budget_exhausted, provider_error
#       requested_at = Column(DateTime(timezone=True), default=func.now())
#       completed_at = Column(DateTime(timezone=True), nullable=True)
#
# This table keeps Document clean and allows re-analysis with full history.
# The idempotency guard checks: if latest AnalysisRequest for this document_id
# has a terminal status (valid, review, rejected, failed), skip.
# The stuck task check queries: AnalysisRequest.status == 'processing'
# AND requested_at < now() - WORKER_STUCK_TASK_MINUTES.
