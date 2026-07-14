from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.enum.crm import DocumentEntityType
from app.schemas.types import RequestUTCDatetime

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


class UploadUrlRequestSchema(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type of the file to upload")
    entity_type: DocumentEntityType
    entity_id: str = Field(..., min_length=1)


class UploadUrlResponseSchema(BaseModel):
    upload_url: str
    key: str
    expires_in: int = 3600


class DocumentConfirmSchema(BaseModel):
    key: str = Field(..., min_length=1, description="R2 key returned from upload-url step")
    type: str = Field(..., min_length=1, max_length=20)
    entity_type: DocumentEntityType
    entity_id: str = Field(..., min_length=1)
    expiry_date: Optional[RequestUTCDatetime] = Field(default=None)


class DocumentResponseSchema(BaseModel):
    id: int
    type: str
    url: str = Field(..., description="Temporary presigned GET URL")
    category: str
    confidence: Optional[float] = None
    extracted_fields: Optional[Any] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
