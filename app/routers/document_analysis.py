from fastapi import APIRouter, Body, Depends, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.document_analysis import AnalysisUploadUrlRequestSchema, AnalysisUploadUrlResponseSchema
from app.services.document_analysis import DocumentAnalysisService

router = APIRouter(prefix="/management/documents/analysis", tags=["Document analysis"])


@router.post(
    "/upload-url",
    response_model=AnalysisUploadUrlResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": (
                "Validation error with a stable `code`: `document_type_not_allowed`, `too_many_files`, "
                "`unsupported_content_type`, `empty_file` or `file_too_large` (the detail includes the limit)."
            ),
            "content": {"application/json": {"example": {"detail": "File 0 exceeds ...", "code": "file_too_large"}}},
        },
        403: {"description": "Only owners and administrators can request uploads."},
    },
)
def request_analysis_upload_url(
    body: AnalysisUploadUrlRequestSchema = Body(...),
    service: DocumentAnalysisService = Depends(ServiceFactory.document_analysis_service),
    user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> AnalysisUploadUrlResponseSchema:
    """Start a temporary analysis and get one presigned PUT URL per file.

    Use it before the vehicle, driver or associate exists. The declared type must be uploadable in a registration
    flow, with at most the files its type allows (INE: front and back). Each file must be PDF, JPEG, PNG or WebP,
    non-empty and at most 15 MB. The browser PUTs each file to its URL with the exact `Content-Type` and
    `Content-Length` declared (both are signed); URLs expire after one hour.

    The returned `analysis_id` is only usable by its creator. It is analyzed by `POST /management/documents/analysis`
    and becomes final documents when a registration section is saved. Not consumed analyses are deleted after 24 h.
    """
    return service.request_upload_urls(body, user)
