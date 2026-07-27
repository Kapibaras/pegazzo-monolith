from fastapi import APIRouter, Body, Depends, Path, status

from app.auth import AuthUser, RequiresAuth
from app.dependencies import ServiceFactory
from app.enum.auth import Role
from app.schemas.image import (
    CarAddPhotoSchema,
    CarAgencyImageSchema,
    CarRemovePhotoSchema,
    DriverPhotoSchema,
    ImageUploadUrlRequestSchema,
    ImageUploadUrlResponseSchema,
)
from app.schemas.user import ActionSuccess
from app.services.image import ImageService

router = APIRouter(prefix="/management/images", tags=["Images"])


@router.post("/upload-url", response_model=ImageUploadUrlResponseSchema, status_code=status.HTTP_200_OK)
def request_upload_url(
    body: ImageUploadUrlRequestSchema = Body(...),
    service: ImageService = Depends(ServiceFactory.image_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ImageUploadUrlResponseSchema:
    """Generate a presigned PUT URL for uploading an image to the public bucket.

    Allowed content types: image/jpeg, image/png, image/webp.
    Returns the presigned PUT URL and the deterministic public URL immediately.
    """
    return service.request_upload_url(body)


@router.patch("/cars/{car_id}/agency-image", response_model=ActionSuccess)
def set_car_agency_image(
    car_id: str = Path(..., description="ID of the car"),
    body: CarAgencyImageSchema = Body(...),
    service: ImageService = Depends(ServiceFactory.image_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Set or replace the agency (hero) image for a car."""
    service.set_car_agency_image(car_id, body)
    return {"message": f"Agency image for car '{car_id}' was successfully updated."}


@router.post("/cars/{car_id}/photos", response_model=ActionSuccess, status_code=status.HTTP_201_CREATED)
def add_car_photo(
    car_id: str = Path(..., description="ID of the car"),
    body: CarAddPhotoSchema = Body(...),
    service: ImageService = Depends(ServiceFactory.image_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Add a photo to the car's photos array. Maximum 4 photos per car."""
    service.add_car_photo(car_id, body)
    return {"message": f"Photo added to car '{car_id}' successfully."}


@router.delete("/cars/{car_id}/photos", response_model=ActionSuccess)
def remove_car_photo(
    car_id: str = Path(..., description="ID of the car"),
    body: CarRemovePhotoSchema = Body(...),
    service: ImageService = Depends(ServiceFactory.image_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Remove a photo URL from the car's photos array."""
    service.remove_car_photo(car_id, body)
    return {"message": f"Photo removed from car '{car_id}' successfully."}


@router.patch("/drivers/{driver_id}/photo", response_model=ActionSuccess)
def set_driver_photo(
    driver_id: str = Path(..., description="ID of the driver"),
    body: DriverPhotoSchema = Body(...),
    service: ImageService = Depends(ServiceFactory.image_service),
    _user: AuthUser = Depends(RequiresAuth([Role.OWNER, Role.ADMIN])),
) -> ActionSuccess:
    """Set or replace the profile photo for a driver."""
    service.set_driver_photo(driver_id, body)
    return {"message": f"Photo for driver '{driver_id}' was successfully updated."}
