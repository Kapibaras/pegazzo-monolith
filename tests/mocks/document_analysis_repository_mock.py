from datetime import UTC, datetime
from uuid import UUID

from app.enum.document import AnalysisStatus
from app.models.document_analysis import DocumentAnalysis


class DocumentAnalysisRepositoryMock:
    """In-memory mock of DocumentAnalysisRepository."""

    def __init__(self):
        """Start with no analyses."""
        self.analyses: dict[UUID, DocumentAnalysis] = {}

    def reset(self):
        """Reset the mock state."""
        self.__init__()

    def create(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """Store the analysis."""
        analysis.created_at = analysis.created_at or datetime.now(UTC)
        self.analyses[analysis.id] = analysis
        return analysis

    def get_many_for_update(self, analysis_ids: list[UUID]) -> dict[UUID, DocumentAnalysis]:
        """Return the stored analyses with the given ids."""
        return {i: self.analyses[i] for i in analysis_ids if i in self.analyses}

    def mark_consumed(self, analysis: DocumentAnalysis, consumed_at: datetime) -> None:
        """Mark the analysis consumed."""
        analysis.status = AnalysisStatus.CONSUMED.value
        analysis.consumed_at = consumed_at

    def list_expired(self, cutoff: datetime) -> list[DocumentAnalysis]:
        """Return not consumed analyses older than cutoff."""
        return [a for a in self.analyses.values() if a.status != AnalysisStatus.CONSUMED.value and a.created_at < cutoff]

    def delete_many(self, analysis_ids: list[UUID]) -> int:
        """Delete the given not consumed analyses."""
        removed = [i for i in analysis_ids if i in self.analyses and self.analyses[i].status != "consumed"]
        for i in removed:
            del self.analyses[i]
        return len(removed)
