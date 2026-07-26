from pydantic import BaseModel, Field

from app.enum.crm import ImageEntityType

ALLOWED_IMAGE_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    },
)

MAX_CAR_PHOTOS = 4


class ImageUploadUrlRequestSchema(BaseModel):
    """Request body for generating a presigned PUT URL for an image."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type — image/jpeg, image/png or image/webp")
    entity_type: ImageEntityType
    entity_id: str = Field(..., min_length=1)


class ImageUploadUrlResponseSchema(BaseModel):
    """Response returned after generating a presigned PUT URL for an image."""

    upload_url: str
    key: str
    public_url: str
    expires_in: int = 3600


class CarAgencyImageSchema(BaseModel):
    """Request body for setting or replacing the car agency image."""

    url: str = Field(..., min_length=1, description="Public URL of the uploaded image")


class CarAddPhotoSchema(BaseModel):
    """Request body for adding a photo to the car photos array."""

    url: str = Field(..., min_length=1, description="Public URL of the uploaded photo")


class CarRemovePhotoSchema(BaseModel):
    """Request body for removing a photo from the car photos array."""

    url: str = Field(..., min_length=1, description="Public URL of the photo to remove")


class DriverPhotoSchema(BaseModel):
    """Request body for setting or replacing the driver profile photo."""

    url: str = Field(..., min_length=1, description="Public URL of the uploaded photo")
