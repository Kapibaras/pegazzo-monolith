from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.documents.registry import is_valid_for_entity
from app.enum.crm import DocumentEntityType
from app.enum.document import DocumentType
from app.schemas.types import RequestUTCDatetime

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    },
)

_VALID_TYPES = {member.value for member in DocumentType}


class UploadUrlRequestSchema(BaseModel):
    """Request body for generating a presigned PUT URL."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type of the file to upload")
    entity_type: DocumentEntityType
    entity_id: str = Field(..., min_length=1)


class UploadUrlResponseSchema(BaseModel):
    """Response returned after generating a presigned PUT URL."""

    upload_url: str
    key: str
    expires_in: int = 3600


class DocumentConfirmSchema(BaseModel):
    """Request body for confirming a document upload and creating the DB record."""

    key: str = Field(..., min_length=1, description="R2 key returned from upload-url step")
    type: str = Field(..., min_length=1, max_length=40)
    entity_type: DocumentEntityType
    entity_id: str = Field(..., min_length=1)
    expiry_date: RequestUTCDatetime | None = Field(default=None)

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        """Validate that *type* is a recognized DocumentType value."""
        if v not in _VALID_TYPES:
            msg = f"Invalid document type '{v}'. Allowed types: {sorted(_VALID_TYPES)}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def type_must_match_entity(self) -> "DocumentConfirmSchema":
        """Validate that *type* is allowed for the given *entity_type*."""
        if not is_valid_for_entity(self.type, self.entity_type.value):
            msg = f"Document type '{self.type}' is not allowed for entity type '{self.entity_type.value}'"
            raise ValueError(msg)
        return self


class DocumentResponseSchema(BaseModel):
    """Response schema for a document record, including a temporary presigned GET URL."""

    id: int
    type: str
    url: str = Field(..., description="Temporary presigned GET URL")
    category: str
    status: str
    extracted_fields: Any | None = None
    expiry_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailSchema(DocumentResponseSchema):
    """Extended response schema for single-document GET with analysis details."""

    detected_type: str | None = None
    review_reasons: Any | None = None
    attempts: int = 0
    analyzed_at: datetime | None = None
    model_version: str | None = None
    error_reason: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None
