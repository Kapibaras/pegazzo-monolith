"""Temporary document analysis: upload URLs and promotion to final documents (PGZ-179).

Lifecycle of an analysis::

    uploaded → analyzed | rejected | failed → consumed
    uploaded → consumed  (evidence-only types, e.g. plates)

Temporary files live under ``private/tmp/analysis/{analysis_id}/{index}.{ext}``. Not consumed analyses older than
24 hours are removed by the cleanup task; the R2 lifecycle rule on ``private/tmp/`` is the safety net.
"""

import uuid

from app.auth import AuthUser
from app.config.constants import DocumentConfig
from app.documents.registry import REGISTRATION_DOCUMENT_TYPES, get_max_files
from app.enum.document import AnalysisStatus
from app.errors.document import InvalidContentTypeException
from app.errors.document_analysis import (
    DocumentTypeNotAllowedException,
    EmptyFileException,
    FileTooLargeException,
    TooManyFilesException,
)
from app.models.document_analysis import DocumentAnalysis
from app.repositories.document import DocumentRepository
from app.repositories.document_analysis import DocumentAnalysisRepository
from app.schemas.document import ALLOWED_CONTENT_TYPES, extension_for
from app.schemas.document_analysis import (
    AnalysisUploadSchema,
    AnalysisUploadUrlRequestSchema,
    AnalysisUploadUrlResponseSchema,
)
from app.storage import r2
from app.utils.logging_config import logger

TMP_PREFIX = "tmp/analysis"


def temp_key(analysis_id: uuid.UUID, index: int, content_type: str) -> str:
    """Return the storage key (without ``private/``) of one temporary file of an analysis."""
    return f"{TMP_PREFIX}/{analysis_id}/{index}.{extension_for(content_type)}"


class DocumentAnalysisService:
    """Service for temporary document analyses."""

    def __init__(self, repository: DocumentAnalysisRepository, document_repository: DocumentRepository):
        """Initialize the service; both repositories must share the request session (one transaction)."""
        self.repository = repository
        self.document_repository = document_repository

    def request_upload_urls(
        self,
        data: AnalysisUploadUrlRequestSchema,
        caller: AuthUser,
    ) -> AnalysisUploadUrlResponseSchema:
        """Validate the declared files, create the analysis and return one presigned PUT URL per file."""
        if data.declared_type not in REGISTRATION_DOCUMENT_TYPES:
            raise DocumentTypeNotAllowedException(data.declared_type)

        max_files = get_max_files(data.declared_type)
        if len(data.files) > max_files:
            raise TooManyFilesException(data.declared_type, max_files)

        for index, file in enumerate(data.files):
            if file.content_type not in ALLOWED_CONTENT_TYPES:
                raise InvalidContentTypeException(file.content_type)
            if file.size <= 0:
                raise EmptyFileException(index)
            if file.size > DocumentConfig.MAX_FILE_BYTES:
                raise FileTooLargeException(index, DocumentConfig.MAX_FILE_BYTES)

        analysis_id = uuid.uuid4()
        files = [
            {"key": temp_key(analysis_id, index, file.content_type), "content_type": file.content_type, "size": file.size}
            for index, file in enumerate(data.files)
        ]
        expires_in = DocumentConfig.PRESIGNED_URL_EXPIRES_SECONDS
        uploads = [
            AnalysisUploadSchema(
                key=f"private/{file['key']}",
                url=r2.generate_document_upload_url(
                    file["key"],
                    file["content_type"],
                    expires_in=expires_in,
                    content_length=file["size"],
                ),
            )
            for file in files
        ]

        self.repository.create(
            DocumentAnalysis(
                id=analysis_id,
                declared_type=data.declared_type,
                files=files,
                status=AnalysisStatus.UPLOADED.value,
                created_by=caller.username,
            ),
        )
        logger.info(
            "Document analysis %s created: type=%s files=%d by=%s",
            analysis_id,
            data.declared_type,
            len(files),
            caller.username,
        )
        return AnalysisUploadUrlResponseSchema(analysis_id=analysis_id, uploads=uploads, expires_in=expires_in)
