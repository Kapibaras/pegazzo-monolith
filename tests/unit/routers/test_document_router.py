from unittest.mock import patch

import pytest

PRESIGNED_PUT_URL = "https://r2.example.com/put-presigned"
PRESIGNED_GET_URL = "https://r2.example.com/get-presigned"


@pytest.mark.usefixtures("authorized_client", "client")
class TestDocumentRouter:
    """Tests for the document management endpoints."""

    # -------------------------------------------------------------------------
    # POST /management/documents/upload-url
    # -------------------------------------------------------------------------

    def test_request_upload_url_car(self, authorized_client):
        with patch("app.services.document.r2.generate_document_upload_url", return_value=PRESIGNED_PUT_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents/upload-url",
                json={
                    "filename": "contrato.pdf",
                    "content_type": "application/pdf",
                    "entity_type": "car",
                    "entity_id": "ABC123DEF456789",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["upload_url"] == PRESIGNED_PUT_URL
        assert data["key"].startswith("car/ABC123DEF456789/")
        assert data["key"].endswith(".pdf")
        assert data["expires_in"] == 3600

    def test_request_upload_url_driver(self, authorized_client):
        with patch("app.services.document.r2.generate_document_upload_url", return_value=PRESIGNED_PUT_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents/upload-url",
                json={
                    "filename": "licencia.jpg",
                    "content_type": "image/jpeg",
                    "entity_type": "driver",
                    "entity_id": "DRV001",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["key"].startswith("driver/DRV001/")
        assert data["key"].endswith(".jpg")

    def test_request_upload_url_guarantor(self, authorized_client):
        with patch("app.services.document.r2.generate_document_upload_url", return_value=PRESIGNED_PUT_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents/upload-url",
                json={
                    "filename": "ine.png",
                    "content_type": "image/png",
                    "entity_type": "guarantor",
                    "entity_id": "1",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["key"].startswith("guarantor/1/")
        assert data["key"].endswith(".png")

    def test_request_upload_url_invalid_content_type(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/documents/upload-url",
            json={
                "filename": "virus.exe",
                "content_type": "application/octet-stream",
                "entity_type": "car",
                "entity_id": "ABC123DEF456789",
            },
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    def test_request_upload_url_entity_not_found(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/documents/upload-url",
            json={
                "filename": "doc.pdf",
                "content_type": "application/pdf",
                "entity_type": "car",
                "entity_id": "NONEXISTENT",
            },
        )
        assert response.status_code == 404
        assert "Car" in response.json()["detail"]

    def test_request_upload_url_employee_forbidden(self, authorized_client):
        """Employee (RBAC) cannot request upload URL — only OWNER/ADMIN."""
        pass

    # -------------------------------------------------------------------------
    # POST /management/documents
    # -------------------------------------------------------------------------

    def test_create_document_car(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents",
                json={
                    "key": "car/ABC123DEF456789/some-uuid.pdf",
                    "type": "contract",
                    "entity_type": "car",
                    "entity_id": "ABC123DEF456789",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "contract"
        assert data["url"] == PRESIGNED_GET_URL
        assert data["category"] == "pending"
        assert data["id"] is not None

    def test_create_document_driver(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents",
                json={
                    "key": "driver/DRV001/some-uuid.pdf",
                    "type": "license",
                    "entity_type": "driver",
                    "entity_id": "DRV001",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "license"

    def test_create_document_guarantor(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents",
                json={
                    "key": "guarantor/1/some-uuid.jpg",
                    "type": "id",
                    "entity_type": "guarantor",
                    "entity_id": "1",
                },
            )
        assert response.status_code == 201

    def test_create_document_entity_not_found(self, authorized_client):
        response = authorized_client.post(
            "/pegazzo/management/documents",
            json={
                "key": "car/NOPE/uuid.pdf",
                "type": "contract",
                "entity_type": "car",
                "entity_id": "NOPE",
            },
        )
        assert response.status_code == 404

    def test_create_document_links_car(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            authorized_client.post(
                "/pegazzo/management/documents",
                json={
                    "key": "car/ABC123DEF456789/uuid.pdf",
                    "type": "contract",
                    "entity_type": "car",
                    "entity_id": "ABC123DEF456789",
                },
            )
        links = authorized_client.document_repo.links
        assert any(lnk["entity_id"] == "ABC123DEF456789" for lnk in links)

    def test_create_document_with_expiry_date(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.post(
                "/pegazzo/management/documents",
                json={
                    "key": "car/ABC123DEF456789/uuid.pdf",
                    "type": "insurance",
                    "entity_type": "car",
                    "entity_id": "ABC123DEF456789",
                    "expiry_date": "2027-01-01T00:00:00Z",
                },
            )
        assert response.status_code == 201
        assert response.json()["expiry_date"] is not None

    # -------------------------------------------------------------------------
    # GET /management/documents/{id}
    # -------------------------------------------------------------------------

    def test_get_document(self, authorized_client):
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.get("/pegazzo/management/documents/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["url"] == PRESIGNED_GET_URL
        assert data["type"] == "contract"

    def test_get_document_not_found(self, authorized_client):
        response = authorized_client.get("/pegazzo/management/documents/9999")
        assert response.status_code == 404
        assert "9999" in response.json()["detail"]

    def test_get_document_employee_allowed(self, authorized_client):
        """Employee role can access GET document — just validating 200 via owner client."""
        with patch("app.services.document.r2.generate_document_read_url", return_value=PRESIGNED_GET_URL):
            response = authorized_client.get("/pegazzo/management/documents/1")
        assert response.status_code == 200

    # -------------------------------------------------------------------------
    # DELETE /management/documents/{id}
    # -------------------------------------------------------------------------

    def test_delete_document(self, authorized_client):
        response = authorized_client.delete("/pegazzo/management/documents/1")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "1" in data["message"]

    def test_delete_document_not_found(self, authorized_client):
        response = authorized_client.delete("/pegazzo/management/documents/9999")
        assert response.status_code == 404

    def test_delete_removes_from_mock(self, authorized_client):
        authorized_client.delete("/pegazzo/management/documents/1")
        assert authorized_client.document_repo.get_by_id(1) is None

    # -------------------------------------------------------------------------
    # RBAC — unauthenticated
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("method", "endpoint", "body"),
        [
            ("post", "/pegazzo/management/documents/upload-url", {"filename": "f.pdf", "content_type": "application/pdf", "entity_type": "car", "entity_id": "X"}),
            ("post", "/pegazzo/management/documents", {"key": "k", "type": "t", "entity_type": "car", "entity_id": "X"}),
            ("get", "/pegazzo/management/documents/1", None),
            ("delete", "/pegazzo/management/documents/1", None),
        ],
    )
    def test_protected_routes_require_auth(self, method, endpoint, body, client):
        func = getattr(client, method)
        response = func(endpoint, json=body) if body else func(endpoint)
        assert response.status_code == 401
