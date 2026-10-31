from app.enum.document import DocumentAnalysisStatus, DocumentCategory, DocumentErrorReason, DocumentType


class TestDocumentEnums:
    """Tests for document-related enums."""

    def test_document_type_member_count(self):
        assert len(DocumentType) == 12

    def test_document_category_member_count(self):
        assert len(DocumentCategory) == 4

    def test_document_analysis_status_member_count(self):
        assert len(DocumentAnalysisStatus) == 9

    def test_document_error_reason_member_count(self):
        assert len(DocumentErrorReason) == 8

    def test_all_enums_are_str(self):
        """StrEnum values must be usable as plain strings."""
        assert DocumentType.INE == "ine"
        assert DocumentCategory.UNCLASSIFIED == "UNCLASSIFIED"
        assert DocumentAnalysisStatus.NOT_ANALYZED == "not_analyzed"
        assert DocumentErrorReason.BLURRY == "blurry"

    def test_document_type_specific_values(self):
        assert DocumentType.CIRCULATION_CARD == "circulation_card"
        assert DocumentType.AMORTIZATION_TABLE == "amortization_table"
        assert DocumentType.UNKNOWN == "unknown"
        assert DocumentType.PROMISSORY_NOTE == "promissory_note"

    def test_document_category_values(self):
        assert DocumentCategory.PEGAZZO == "PEGAZZO"
        assert DocumentCategory.PEGAZZO_ASSOCIATE == "PEGAZZO_ASSOCIATE"
        assert DocumentCategory.THIRD_PARTY == "THIRD_PARTY"

    def test_document_analysis_status_values(self):
        assert DocumentAnalysisStatus.PENDING == "pending"
        assert DocumentAnalysisStatus.PROCESSING == "processing"
        assert DocumentAnalysisStatus.SUPERSEDED == "superseded"
        assert DocumentAnalysisStatus.ACCEPTED == "accepted"
