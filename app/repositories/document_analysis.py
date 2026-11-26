from datetime import datetime
from uuid import UUID

from app.enum.document import AnalysisStatus
from app.errors.database import DBOperationError
from app.models.document_analysis import DocumentAnalysis
from app.utils.logging_config import logger

from .abstract import DBRepository


class DocumentAnalysisRepository(DBRepository):
    """Repository for temporary document analyses."""

    def create(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Persist a new analysis (own transaction: the upload URL request has nothing else to save)."""
        try:
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
        except Exception as ex:
            self.db.rollback()
            logger.error("Error creating document analysis %s: %s", analysis.id, ex)
            raise DBOperationError("Error creating document analysis in the database") from ex
        return analysis

    def get_many_for_update(self, analysis_ids: list[UUID]) -> dict[UUID, DocumentAnalysis]:
        """Return the analyses with the given ids, row-locked until the caller's transaction ends.

        The lock (``SELECT ... FOR UPDATE``) stops two concurrent saves from promoting the same analysis twice.
        """
        if not analysis_ids:
            return {}
        rows = (
            self.db.query(DocumentAnalysis)
            .filter(DocumentAnalysis.id.in_(analysis_ids))
            .order_by(DocumentAnalysis.id)
            .with_for_update()
            .all()
        )
        return {row.id: row for row in rows}

    def mark_consumed(self, analysis: DocumentAnalysis, consumed_at: datetime) -> None:
        """Mark an analysis as consumed; only flushed, the caller commits."""
        try:
            analysis.status = AnalysisStatus.CONSUMED.value
            analysis.consumed_at = consumed_at
            self.db.flush()
        except Exception as ex:
            logger.error("Error marking document analysis %s as consumed: %s", analysis.id, ex)
            raise DBOperationError("Error updating document analysis in the database") from ex

    def list_expired(self, cutoff: datetime) -> list[DocumentAnalysis]:
        """Return the not consumed analyses created before *cutoff* (uses the (status, created_at) index)."""
        return (
            self.db.query(DocumentAnalysis)
            .filter(
                DocumentAnalysis.status != AnalysisStatus.CONSUMED.value,
                DocumentAnalysis.created_at < cutoff,
            )
            .all()
        )

    def delete_many(self, analysis_ids: list[UUID]) -> int:
        """Delete the analyses with the given ids that are still not consumed; return how many were removed."""
        if not analysis_ids:
            return 0
        try:
            deleted = (
                self.db.query(DocumentAnalysis)
                .filter(
                    DocumentAnalysis.id.in_(analysis_ids),
                    DocumentAnalysis.status != AnalysisStatus.CONSUMED.value,
                )
                .delete(synchronize_session=False)
            )
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Error deleting expired document analyses: %s", ex)
            raise DBOperationError("Error deleting document analyses from the database") from ex
        return deleted
