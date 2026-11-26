"""Temporary document analysis: upload URLs and promotion to final documents (PGZ-179).

Lifecycle of an analysis::

    uploaded → analyzed | rejected | failed → consumed
    uploaded → consumed  (evidence-only types, e.g. plates)

Temporary files live under ``private/tmp/analysis/{analysis_id}/{index}.{ext}``. Not consumed analyses older than
24 hours are removed by the cleanup task; the R2 lifecycle rule on ``private/tmp/`` is the safety net.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.auth import AuthUser
from app.config.constants import DocumentConfig
from app.documents.registry import REGISTRATION_DOCUMENT_TYPES, get_max_files, is_ai_analyzable, is_valid_for_entity
from app.enum.auth import Role
from app.enum.crm import DocumentEntityType
from app.enum.document import AnalysisStatus, DocumentAnalysisStatus, DocumentCategory, DocumentErrorReason
from app.errors.document import InvalidContentTypeException
from app.errors.document_analysis import (
    AnalysisConsumedException,
    AnalysisDuplicatedException,
    AnalysisFileMissingException,
    AnalysisNotAnalyzedException,
    AnalysisNotFoundException,
    DocumentTypeNotAllowedException,
    EmptyFileException,
    FileTooLargeException,
    ManualEntryNotAllowedException,
    ManualEntryRequiresOwnerException,
    TooManyFilesException,
)
from app.models.document import Document
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


@dataclass(frozen=True)
class FinalValues:
    """What the person saved in the section for one analysis: the confirmed fields and the expiry date."""

    fields: dict[str, Any] = field(default_factory=dict)
    expiry_date: datetime | None = None


@dataclass
class PromotionResult:
    """Outcome of ``promote_analyses``: what to clean up after the caller's commit or rollback."""

    documents: list[Document] = field(default_factory=list)
    temp_keys: list[str] = field(default_factory=list)
    final_keys: list[str] = field(default_factory=list)


def finalize_promotion(result: PromotionResult) -> None:
    """After the caller committed: delete the temporary files (best effort; the R2 lifecycle rule is the safety net)."""
    r2.delete_documents_best_effort(result.temp_keys)


def rollback_promotion(result: PromotionResult) -> None:
    """After the caller rolled back: delete the copied final files (best effort). Temporary files stay for a retry."""
    r2.delete_documents_best_effort(result.final_keys)


def _evaluation_fields(ai_fields: dict[str, Any] | None, saved: dict[str, Any]) -> dict[str, Any]:
    """Return ``{field: {"value": <AI>, "check": <AI check>, "final": <saved>}}`` (evaluation data for PGZ-166).

    Accepts AI fields stored as ``{"value": ..., "check": ...}`` or as a bare value.
    """
    ai_fields = ai_fields or {}
    result = {}
    for name in [*ai_fields, *(n for n in saved if n not in ai_fields)]:
        ai = ai_fields.get(name)
        if isinstance(ai, dict) and "value" in ai:
            value, check = ai.get("value"), ai.get("check")
        else:
            value, check = ai, None
        result[name] = {"value": value, "check": check, "final": saved.get(name)}
    return result


def _prefill_expiry(analysis: DocumentAnalysis) -> datetime | None:
    """Return ``prefill["expiry_date"]`` (ISO date or datetime) as a UTC datetime, or ``None``."""
    raw = (analysis.prefill or {}).get("expiry_date")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw))
    except ValueError:
        logger.warning("Analysis %s has an invalid prefill expiry date", analysis.id)
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _can_be_entered_manually(analysis: DocumentAnalysis) -> bool:
    if analysis.status == AnalysisStatus.FAILED.value:
        return True
    return analysis.status == AnalysisStatus.REJECTED.value and analysis.reason != DocumentErrorReason.WRONG_DOCUMENT


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

    def promote_analyses(
        self,
        *,
        entity_type: DocumentEntityType,
        entity_id: str,
        analysis_ids: list[uuid.UUID],
        manual_analysis_ids: list[uuid.UUID],
        allowed_types: set[str],
        final_values: dict[uuid.UUID, FinalValues],
        caller: AuthUser,
    ) -> PromotionResult:
        """Turn confirmed analyses into final documents of an entity, inside the caller's transaction.

        Never commits: documents, links and the ``consumed`` status are only flushed. Order: validate everything →
        copy the files to their final keys → DB writes → (caller commits) → ``finalize_promotion`` deletes the
        temporary files. If the caller's commit or anything after this call fails, the caller rolls back and calls
        ``rollback_promotion``. If this call itself fails, it removes the files it already copied before raising, so
        nothing is created and the temporary files stay for a retry.
        """
        manual_ids = set(manual_analysis_ids)
        if manual_ids and caller.role != Role.OWNER:
            raise ManualEntryRequiresOwnerException

        requested = [*analysis_ids, *manual_analysis_ids]
        seen: set[uuid.UUID] = set()
        for analysis_id in requested:
            if analysis_id in seen:
                raise AnalysisDuplicatedException(analysis_id)
            seen.add(analysis_id)

        analyses = self.repository.get_many_for_update(requested)
        selected = [
            self._validate_for_promotion(analyses.get(i), i, entity_type, allowed_types, caller, manual=i in manual_ids)
            for i in requested
        ]

        for analysis in selected:
            for index, file in enumerate(analysis.files):
                if r2.head_document(file["key"]) is None:
                    raise AnalysisFileMissingException(analysis.id, index)

        result = PromotionResult()
        try:
            planned: list[tuple[DocumentAnalysis, dict, str]] = []
            for analysis in selected:
                for file in analysis.files:
                    final_key = f"{entity_type.value}/{entity_id}/{uuid.uuid4()}.{extension_for(file['content_type'])}"
                    r2.copy_document(file["key"], final_key)
                    result.final_keys.append(final_key)
                    planned.append((analysis, file, final_key))

            now = datetime.now(UTC)
            for analysis, file, final_key in planned:
                document = self._build_document(
                    analysis,
                    final_key,
                    final_values.get(analysis.id) or FinalValues(),
                    caller,
                    now,
                    manual=analysis.id in manual_ids,
                )
                self.document_repository.create(document, commit=False)
                self._link(document.id, entity_type, entity_id)
                result.documents.append(document)
                result.temp_keys.append(file["key"])

            for analysis in selected:
                self.repository.mark_consumed(analysis, now)
        except Exception:
            rollback_promotion(result)
            raise

        logger.info(
            "Promoted %d analyses (%d manual) to %d documents of %s %s by %s",
            len(selected),
            len(manual_ids),
            len(result.documents),
            entity_type.value,
            entity_id,
            caller.username,
        )
        return result

    @staticmethod
    def _validate_for_promotion(
        analysis: DocumentAnalysis | None,
        analysis_id: uuid.UUID,
        entity_type: DocumentEntityType,
        allowed_types: set[str],
        caller: AuthUser,
        *,
        manual: bool,
    ) -> DocumentAnalysis:
        if analysis is None or analysis.created_by != caller.username:
            raise AnalysisNotFoundException(analysis_id)
        if analysis.status == AnalysisStatus.CONSUMED.value:
            raise AnalysisConsumedException(analysis_id)
        if analysis.declared_type not in allowed_types or not is_valid_for_entity(
            analysis.declared_type,
            entity_type.value,
        ):
            raise DocumentTypeNotAllowedException(analysis.declared_type, f"this {entity_type.value} section")
        if manual:
            if not _can_be_entered_manually(analysis):
                raise ManualEntryNotAllowedException(analysis_id)
        elif is_ai_analyzable(analysis.declared_type):
            if analysis.status != AnalysisStatus.ANALYZED.value:
                raise AnalysisNotAnalyzedException(analysis_id, analysis.status)
        elif analysis.status != AnalysisStatus.UPLOADED.value:
            raise AnalysisNotAnalyzedException(analysis_id, analysis.status)
        return analysis

    @staticmethod
    def _build_document(
        analysis: DocumentAnalysis,
        final_key: str,
        final: FinalValues,
        caller: AuthUser,
        now: datetime,
        *,
        manual: bool,
    ) -> Document:
        """Build the final document of one file, with the status and verification of its kind of promotion."""
        document = Document(
            type=analysis.declared_type,
            url=final_key,
            category=DocumentCategory.UNCLASSIFIED.value,
            analysis_id=analysis.id,
            detected_type=analysis.detected_type,
            model_version=analysis.model_version,
            analyzed_at=analysis.analyzed_at,
            attempts=0,
        )
        if manual:
            # The file is evidence only; every field of the section was typed by the owner.
            document.status = DocumentAnalysisStatus.NOT_ANALYZED.value
            document.extracted_fields = None
            document.expiry_date = final.expiry_date
            document.verified_by = caller.username
            document.verified_at = now
        elif is_ai_analyzable(analysis.declared_type):
            # The person confirmed the extracted data by saving the section.
            document.status = DocumentAnalysisStatus.VALID.value
            document.extracted_fields = _evaluation_fields(analysis.extracted_fields, final.fields)
            document.expiry_date = final.expiry_date or _prefill_expiry(analysis)
            document.verified_by = caller.username
            document.verified_at = now
        else:
            document.status = DocumentAnalysisStatus.NOT_ANALYZED.value
            document.extracted_fields = None
            document.expiry_date = final.expiry_date
        return document

    def _link(self, document_id: int, entity_type: DocumentEntityType, entity_id: str) -> None:
        if entity_type == DocumentEntityType.CAR:
            self.document_repository.link_to_car(document_id, entity_id, commit=False)
        elif entity_type == DocumentEntityType.DRIVER:
            self.document_repository.link_to_driver(document_id, entity_id, commit=False)
        elif entity_type == DocumentEntityType.GUARANTOR:
            self.document_repository.link_to_guarantor(document_id, int(entity_id), commit=False)
        elif entity_type == DocumentEntityType.GARAGE:
            self.document_repository.link_to_garage(document_id, int(entity_id), commit=False)
