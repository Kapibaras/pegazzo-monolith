from unittest.mock import patch

import pytest

PRESIGNED_PUT_URL = "https://r2.example.com/image-presigned-put"
PUBLIC_URL = "https://pub.example.com/car_photo/CAR001/some-uuid.jpg"

CAR_ID = "CAR001"
DRIVER_ID = "DRV001"


@pytest.mark.usefixtures("authorized_client", "client")
class TestImageRouter:
    """Tests for the image management endpoints."""

    # -------------------------------------------------------------------------
    # POST /management/images/upload-url
    # -------------------------------------------------------------------------

    def test_request_upload_url_car_photo(self, authorized_client):
        with (
            patch("app.services.image.r2.generate_image_upload_url", return_value=PRESIGNED_PUT_URL),
            patch("app.services.image.r2.get_image_public_url", return_value=PUBLIC_URL),
        ):
            response = authorized_client.post(
                "/pegazzo/management/images/upload-url",
                json={
                    "filename": "photo.jpg",
                    "content_type": "image/jpeg",
                    "entity_type": "car_photo",
                    "entity_id": CAR_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["upload_url"] == PRESIGNED_PUT_URL
        assert data["public_url"] == PUBLIC_URL
        assert data["key"].startswith("car_photo/CAR001/")
        assert data["key"].endswith(".jpg")
        assert data["expires_in"] == 3600

    def test_request_upload_url_car_agency_image(self, authorized_client):
        with (
            patch("app.services.image.r2.generate_image_upload_url", return_value=PRESIGNED_PUT_URL),
            patch("app.services.image.r2.get_image_public_url", return_value=PUBLIC_URL),
        ):
            response = authorized_client.post(
                "/pegazzo/management/images/upload-url",
                json={
                    "filename": "agency.png",
                    "content_type": "image/png",
                    "entity_type": "car_agency_image",
                    "entity_id": CAR_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["key"].startswith("car_agency_image/CAR001/")
        assert data["key"].endswith(".png")

    def test_request_upload_url_driver_photo(self, authorized_client):
        with (
            patch("app.services.image.r2.generate_image_upload_url", return_value=PRESIGNED_PUT_URL),
            patch("app.services.image.r2.get_image_public_url", return_value=PUBLIC_URL),
        ):
            response = authorized_client.post(
                "/pegazzo/management/images/upload-url",
                json={
                    "filename": "driver.webp",
                    "content_type": "image/webp",
                    "entity_type": "driver_photo",
                    "entity_id": DRIVER_ID,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["key"].startswith("driver_photo/DRV001/")
        assert data["key"].endswith(".webp")

    def test_request_upload_url_invalid_content_type(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/images/upload-url",
            json={
                "filename": "file.gif",
                "content_type": "image/gif",
                "entity_type": "car_photo",
                "entity_id": CAR_ID,
            },
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    def test_request_upload_url_car_not_found(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/images/upload-url",
            json={
                "filename": "photo.jpg",
                "content_type": "image/jpeg",
                "entity_type": "car_photo",
                "entity_id": "NONEXISTENT",
            },
        )
        assert response.status_code == 404
        assert "car" in response.json()["detail"].lower()

    def test_request_upload_url_driver_not_found(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/images/upload-url",
            json={
                "filename": "photo.jpg",
                "content_type": "image/jpeg",
                "entity_type": "driver_photo",
                "entity_id": "NONEXISTENT",
            },
        )
        assert response.status_code == 404
        assert "driver" in response.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # PATCH /management/images/cars/{car_id}/agency-image
    # -------------------------------------------------------------------------

    def test_set_car_agency_image(self, authorized_client):
        response = authorized_client.patch(
            f"/pegazzo/management/images/cars/{CAR_ID}/agency-image",
            json={"url": "car_agency_image/CAR001/uuid.jpg"},
        )
        assert response.status_code == 200
        assert "agency image" in response.json()["message"].lower()
        assert authorized_client.image_repo.get_car_by_id(CAR_ID).agency_image == "car_agency_image/CAR001/uuid.jpg"

    def test_set_car_agency_image_car_not_found(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/images/cars/NOPE/agency-image",
            json={"url": "some/url.jpg"},
        )
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # POST /management/images/cars/{car_id}/photos
    # -------------------------------------------------------------------------

    def test_add_car_photo(self, authorized_client):
        response = authorized_client.post(
            f"/pegazzo/management/images/cars/{CAR_ID}/photos",
            json={"url": "car_photo/CAR001/uuid1.jpg"},
        )
        assert response.status_code == 201
        assert "photo added" in response.json()["message"].lower()
        assert "car_photo/CAR001/uuid1.jpg" in authorized_client.image_repo.get_car_by_id(CAR_ID).photos

    def test_add_car_photo_max_exceeded(self, authorized_client):
        car = authorized_client.image_repo.get_car_by_id(CAR_ID)
        car.photos = ["url1.jpg", "url2.jpg", "url3.jpg", "url4.jpg"]

        response = authorized_client.post(
            f"/pegazzo/management/images/cars/{CAR_ID}/photos",
            json={"url": "url5.jpg"},
        )
        assert response.status_code == 400
        assert "4" in response.json()["detail"]

    def test_add_car_photo_car_not_found(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/images/cars/NOPE/photos",
            json={"url": "some/url.jpg"},
        )
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # DELETE /management/images/cars/{car_id}/photos
    # -------------------------------------------------------------------------

    def test_remove_car_photo(self, authorized_client):
        car = authorized_client.image_repo.get_car_by_id(CAR_ID)
        car.photos = ["car_photo/CAR001/to-remove.jpg"]

        response = authorized_client.request(
            "DELETE",
            f"/pegazzo/management/images/cars/{CAR_ID}/photos",
            json={"url": "car_photo/CAR001/to-remove.jpg"},
        )
        assert response.status_code == 200
        assert "car_photo/CAR001/to-remove.jpg" not in authorized_client.image_repo.get_car_by_id(CAR_ID).photos

    def test_remove_car_photo_not_found(self, authorized_client):
        response = authorized_client.request(
            "DELETE",
            f"/pegazzo/management/images/cars/{CAR_ID}/photos",
            json={"url": "nonexistent.jpg"},
        )
        assert response.status_code == 404

    def test_remove_car_photo_car_not_found(self, authorized_client):
        response = authorized_client.request(
            "DELETE",
            "/pegazzo/management/images/cars/NOPE/photos",
            json={"url": "some/url.jpg"},
        )
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # PATCH /management/images/drivers/{driver_id}/photo
    # -------------------------------------------------------------------------

    def test_set_driver_photo(self, authorized_client):
        response = authorized_client.patch(
            f"/pegazzo/management/images/drivers/{DRIVER_ID}/photo",
            json={"url": "driver_photo/DRV001/uuid.jpg"},
        )
        assert response.status_code == 200
        assert "photo" in response.json()["message"].lower()
        assert authorized_client.image_repo.get_driver_by_id(DRIVER_ID).photo == "driver_photo/DRV001/uuid.jpg"

    def test_set_driver_photo_driver_not_found(self, authorized_client):
        response = authorized_client.patch(
            "/pegazzo/management/images/drivers/NOPE/photo",
            json={"url": "some/url.jpg"},
        )
        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # RBAC — unauthenticated
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("method", "endpoint", "body"),
        [
            ("post", "/pegazzo/management/images/upload-url", {"filename": "f.jpg", "content_type": "image/jpeg", "entity_type": "car_photo", "entity_id": "X"}),
            ("patch", f"/pegazzo/management/images/cars/{CAR_ID}/agency-image", {"url": "u"}),
            ("post", f"/pegazzo/management/images/cars/{CAR_ID}/photos", {"url": "u"}),
            ("DELETE", f"/pegazzo/management/images/cars/{CAR_ID}/photos", {"url": "u"}),
            ("patch", f"/pegazzo/management/images/drivers/{DRIVER_ID}/photo", {"url": "u"}),
        ],
    )
    def test_protected_routes_require_auth(self, method, endpoint, body, client):
        if method == "DELETE":
            response = client.request("DELETE", endpoint, json=body)
        else:
            func = getattr(client, method)
            response = func(endpoint, json=body)
        assert response.status_code == 401
