import uuid

from app.enum.crm import ImageEntityType
from app.errors.image import (
    ImageEntityNotFoundException,
    InvalidImageTypeException,
    MaxPhotosExceededException,
    PhotoNotFoundException,
)
from app.repositories.image import ImageRepository
from app.schemas.image import (
    ALLOWED_IMAGE_CONTENT_TYPES,
    MAX_CAR_PHOTOS,
    CarAddPhotoSchema,
    CarAgencyImageSchema,
    CarRemovePhotoSchema,
    DriverPhotoSchema,
    ImageUploadUrlRequestSchema,
    ImageUploadUrlResponseSchema,
)
from app.storage import r2


def _extension_for(content_type: str) -> str:
    """Return the file extension for a given image MIME type."""
    extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    return extensions.get(content_type, "jpg")


class ImageService:
    """Image service class."""

    def __init__(self, repository: ImageRepository):
        """Initialize the image service with a repository."""
        self.repository = repository

    def request_upload_url(self, data: ImageUploadUrlRequestSchema) -> ImageUploadUrlResponseSchema:
        """Validate the request and return a presigned PUT URL plus the deterministic public URL."""
        if data.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise InvalidImageTypeException(data.content_type)

        self._assert_entity_exists(data.entity_type, data.entity_id)

        ext = _extension_for(data.content_type)
        key = f"{data.entity_type}/{data.entity_id}/{uuid.uuid4()}.{ext}"
        upload_url = r2.generate_image_upload_url(key, data.content_type)
        public_url = r2.get_image_public_url(key)

        return ImageUploadUrlResponseSchema(upload_url=upload_url, key=key, public_url=public_url, expires_in=3600)

    def set_car_agency_image(self, car_id: str, data: CarAgencyImageSchema):
        """Set or replace the agency image for a car."""
        car = self.repository.get_car_by_id(car_id)
        if not car:
            raise ImageEntityNotFoundException("car", car_id)
        return self.repository.set_car_agency_image(car, data.url)

    def add_car_photo(self, car_id: str, data: CarAddPhotoSchema):
        """Add a photo to the car's photos array, enforcing the max 4 limit."""
        car = self.repository.get_car_by_id(car_id)
        if not car:
            raise ImageEntityNotFoundException("car", car_id)
        if len(car.photos or []) >= MAX_CAR_PHOTOS:
            raise MaxPhotosExceededException
        return self.repository.add_car_photo(car, data.url)

    def remove_car_photo(self, car_id: str, data: CarRemovePhotoSchema):
        """Remove a photo URL from the car's photos array."""
        car = self.repository.get_car_by_id(car_id)
        if not car:
            raise ImageEntityNotFoundException("car", car_id)
        if data.url not in (car.photos or []):
            raise PhotoNotFoundException
        return self.repository.remove_car_photo(car, data.url)

    def set_driver_photo(self, driver_id: str, data: DriverPhotoSchema):
        """Set or replace the profile photo for a driver."""
        driver = self.repository.get_driver_by_id(driver_id)
        if not driver:
            raise ImageEntityNotFoundException("driver", driver_id)
        return self.repository.set_driver_photo(driver, data.url)

    def _assert_entity_exists(self, entity_type: ImageEntityType, entity_id: str) -> None:
        """Raise ImageEntityNotFoundException if the target entity does not exist."""
        if entity_type in (ImageEntityType.CAR_AGENCY_IMAGE, ImageEntityType.CAR_PHOTO):
            if not self.repository.get_car_by_id(entity_id):
                raise ImageEntityNotFoundException("car", entity_id)
        elif entity_type == ImageEntityType.DRIVER_PHOTO and not self.repository.get_driver_by_id(entity_id):
            raise ImageEntityNotFoundException("driver", entity_id)
