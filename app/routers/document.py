from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.document import DocumentConfirmSchema, DocumentResponseSchema, UploadUrlRequestSchema, UploadUrlResponseSchema
from app.schemas.user import ActionSuccess
from app.services.document import DocumentService

router = APIRouter(prefix="/management/documents", tags=["Documents"])


@router.post("/upload-url", response_model=UploadUrlResponseSchema, status_code=status.HTTP_200_OK)
def request_upload_url(
    body: UploadUrlRequestSchema = Body(...),
    service: DocumentService = Depends(ServiceFactory.document_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> UploadUrlResponseSchema:
    """Generate a presigned PUT URL for uploading a document to private storage.

    Allowed content types: application/pdf, image/jpeg, image/png, image/webp.
    The client must PUT the file binary directly to the returned URL before confirming.
    """
    return service.request_upload_url(body)


@router.post("", response_model=DocumentResponseSchema, status_code=status.HTTP_201_CREATED)
def create_document(
    body: DocumentConfirmSchema = Body(...),
    service: DocumentService = Depends(ServiceFactory.document_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> DocumentResponseSchema:
    """Create a Document record and link it to the target entity after uploading the file."""
    return service.create_document(body)


@router.get("/{document_id}", response_model=DocumentResponseSchema)
def get_document(
    document_id: int = Path(..., description="ID of the document"),
    service: DocumentService = Depends(ServiceFactory.document_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN, Role.EMPLOYEE])),
) -> DocumentResponseSchema:
    """Get document metadata and a temporary presigned download URL."""
    return service.get_document(document_id)


@router.delete("/{document_id}", response_model=ActionSuccess)
def delete_document(
    document_id: int = Path(..., description="ID of the document"),
    service: DocumentService = Depends(ServiceFactory.document_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Delete a document record."""
    service.delete_document(document_id)
    return {"message": f"Document '{document_id}' was successfully deleted."}
