"""Errors of the temporary document analysis flow (PGZ-179).

Every error carries a stable ``code`` the frontend can rely on; ``detail`` is human readable and may change.
"""

from fastapi import status

from app.errors import PegazzoException


class DocumentTypeNotAllowedException(PegazzoException):
    """Raised when a document type cannot be uploaded in a registration flow or is not allowed for a section/entity."""

    def __init__(self, doc_type: str, scope: str = "a registration flow"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document type '{doc_type}' is not allowed for {scope}",
            code="document_type_not_allowed",
        )


class TooManyFilesException(PegazzoException):
    """Raised when an upload has more files than its document type allows."""

    def __init__(self, doc_type: str, max_files: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document type '{doc_type}' accepts at most {max_files} file(s)",
            code="too_many_files",
        )


class EmptyFileException(PegazzoException):
    """Raised when a declared file size is zero or negative."""

    def __init__(self, index: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {index} is empty",
            code="empty_file",
        )


class FileTooLargeException(PegazzoException):
    """Raised when a declared file size exceeds the document limit."""

    def __init__(self, index: int, max_bytes: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {index} exceeds the maximum size of {max_bytes} bytes ({max_bytes // (1024 * 1024)} MB)",
            code="file_too_large",
        )


class AnalysisNotFoundException(PegazzoException):
    """Raised when an analysis does not exist or belongs to another user (never reveals which)."""

    def __init__(self, analysis_id: object):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' was not found",
            code="analysis_not_found",
        )


class AnalysisConsumedException(PegazzoException):
    """Raised when an analysis was already promoted to final documents."""

    def __init__(self, analysis_id: object):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Analysis '{analysis_id}' was already used",
            code="analysis_consumed",
        )


class AnalysisNotAnalyzedException(PegazzoException):
    """Raised when an analyzable document is promoted without a successful analysis."""

    def __init__(self, analysis_id: object, analysis_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis '{analysis_id}' is '{analysis_status}' and cannot be saved without a successful analysis",
            code="analysis_not_analyzed",
        )


class AnalysisFileMissingException(PegazzoException):
    """Raised when a temporary file of an analysis is not in storage (never uploaded or already cleaned up)."""

    def __init__(self, analysis_id: object, index: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {index} of analysis '{analysis_id}' was not uploaded or has expired",
            code="analysis_file_missing",
        )


class AnalysisDuplicatedException(PegazzoException):
    """Raised when the same analysis is sent more than once in a promotion."""

    def __init__(self, analysis_id: object):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis '{analysis_id}' was sent more than once",
            code="analysis_duplicated",
        )


class ManualEntryRequiresOwnerException(PegazzoException):
    """Raised when a non-owner sends manual-entry analyses."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an owner can save a document with manually typed data",
            code="manual_entry_requires_owner",
        )


class ManualEntryNotAllowedException(PegazzoException):
    """Raised when an analysis cannot be saved by manual entry (not failed, or rejected as a wrong document)."""

    def __init__(self, analysis_id: object):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis '{analysis_id}' cannot be saved by manual entry",
            code="manual_entry_not_allowed",
        )
