from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisFileSchema(BaseModel):
    """One file the browser is about to upload."""

    content_type: str = Field(..., description="MIME type: application/pdf, image/jpeg, image/png or image/webp")
    size: int = Field(..., description="Exact size in bytes; it is signed in the upload URL")


class AnalysisUploadUrlRequestSchema(BaseModel):
    """Request body to start a temporary analysis and get one presigned PUT URL per file."""

    declared_type: str = Field(..., min_length=1, max_length=40, description="Document type, e.g. 'ine'")
    files: list[AnalysisFileSchema] = Field(..., min_length=1, max_length=10)


class AnalysisUploadSchema(BaseModel):
    """Where to PUT one file."""

    key: str = Field(..., description="Storage key of the temporary file")
    url: str = Field(..., description="Presigned PUT URL; send the exact Content-Type and Content-Length declared")


class AnalysisUploadUrlResponseSchema(BaseModel):
    """Response with the analysis id and the presigned PUT URLs, in the order of the request files."""

    analysis_id: UUID
    uploads: list[AnalysisUploadSchema]
    expires_in: int = Field(..., description="Seconds until the upload URLs expire")
