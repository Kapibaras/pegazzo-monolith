from unittest.mock import patch
from uuid import UUID

import pytest

from app.config.constants import DocumentConfig

URL = "/pegazzo/management/documents/analysis/upload-url"
PRESIGNED_PUT_URL = "https://r2.example.com/put-presigned"
SIGNER = "app.services.document_analysis.r2.generate_document_upload_url"


def _body(declared_type="ine", files=None):
    return {"declared_type": declared_type, "files": files or [{"content_type": "image/jpeg", "size": 2400000}]}


@pytest.fixture
def signer():
    with patch(SIGNER, return_value=PRESIGNED_PUT_URL) as mock_signer:
        yield mock_signer


class TestAnalysisUploadUrl:
    """POST /management/documents/analysis/upload-url."""

    def test_single_file(self, authorized_client, signer):
        response = authorized_client.post(URL, json=_body("invoice", [{"content_type": "application/pdf", "size": 1000}]))

        assert response.status_code == 200
        data = response.json()
        analysis_id = UUID(data["analysis_id"])
        assert data["expires_in"] == 3600
        assert data["uploads"] == [
            {"key": f"private/tmp/analysis/{analysis_id}/0.pdf", "url": PRESIGNED_PUT_URL},
        ]
        signer.assert_called_once_with(
            f"tmp/analysis/{analysis_id}/0.pdf",
            "application/pdf",
            expires_in=3600,
            content_length=1000,
        )

        analysis = authorized_client.document_analysis_repo.analyses[analysis_id]
        assert analysis.status == "uploaded"
        assert analysis.declared_type == "invoice"
        assert analysis.created_by == "testuser"
        assert analysis.files == [
            {"key": f"tmp/analysis/{analysis_id}/0.pdf", "content_type": "application/pdf", "size": 1000},
        ]

    def test_ine_with_two_files(self, authorized_client, signer):
        files = [{"content_type": "image/jpeg", "size": 2400000}, {"content_type": "image/png", "size": 1800000}]

        response = authorized_client.post(URL, json=_body("ine", files))

        assert response.status_code == 200
        data = response.json()
        analysis_id = data["analysis_id"]
        assert [u["key"] for u in data["uploads"]] == [
            f"private/tmp/analysis/{analysis_id}/0.jpg",
            f"private/tmp/analysis/{analysis_id}/1.png",
        ]
        assert [c.kwargs["content_length"] for c in signer.call_args_list] == [2400000, 1800000]

    def test_evidence_only_type_is_accepted(self, authorized_client, signer):
        response = authorized_client.post(URL, json=_body("plates"))

        assert response.status_code == 200
        signer.assert_called_once()

    def test_admin_is_allowed(self, admin_authorized_client, signer):
        response = admin_authorized_client.post(URL, json=_body())

        assert response.status_code == 200
        signer.assert_called_once()

    def test_employee_is_forbidden(self, employee_authorized_client, signer):
        response = employee_authorized_client.post(URL, json=_body())

        assert response.status_code == 403
        signer.assert_not_called()

    def test_unauthenticated(self, client, signer):
        response = client.post(URL, json=_body())

        assert response.status_code == 401
        signer.assert_not_called()

    def test_empty_file(self, authorized_client, signer):
        response = authorized_client.post(URL, json=_body(files=[{"content_type": "image/jpeg", "size": 0}]))

        assert response.status_code == 400
        assert response.json()["code"] == "empty_file"
        signer.assert_not_called()
        assert authorized_client.document_analysis_repo.analyses == {}

    def test_file_too_large_includes_limit(self, authorized_client, signer):
        size = DocumentConfig.MAX_FILE_BYTES + 1
        response = authorized_client.post(URL, json=_body(files=[{"content_type": "image/jpeg", "size": size}]))

        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "file_too_large"
        assert str(DocumentConfig.MAX_FILE_BYTES) in body["detail"]
        signer.assert_not_called()

    def test_file_at_limit_is_accepted(self, authorized_client, signer):
        size = DocumentConfig.MAX_FILE_BYTES
        response = authorized_client.post(URL, json=_body(files=[{"content_type": "image/jpeg", "size": size}]))

        assert response.status_code == 200
        signer.assert_called_once()

    def test_unsupported_content_type(self, authorized_client, signer):
        response = authorized_client.post(URL, json=_body(files=[{"content_type": "image/gif", "size": 100}]))

        assert response.status_code == 400
        assert response.json()["code"] == "unsupported_content_type"
        signer.assert_not_called()

    @pytest.mark.parametrize("declared_type", ["contract", "promissory_note", "unknown", "not_a_type"])
    def test_type_not_allowed(self, authorized_client, signer, declared_type):
        response = authorized_client.post(URL, json=_body(declared_type))

        assert response.status_code == 400
        assert response.json()["code"] == "document_type_not_allowed"
        signer.assert_not_called()

    def test_too_many_files(self, authorized_client, signer):
        files = [{"content_type": "image/jpeg", "size": 100}] * 2

        response = authorized_client.post(URL, json=_body("invoice", files))

        assert response.status_code == 400
        assert response.json()["code"] == "too_many_files"
        signer.assert_not_called()

    def test_ine_with_three_files_is_too_many(self, authorized_client, signer):
        files = [{"content_type": "image/jpeg", "size": 100}] * 3

        response = authorized_client.post(URL, json=_body("ine", files))

        assert response.status_code == 400
        assert response.json()["code"] == "too_many_files"
        signer.assert_not_called()

    def test_no_files_is_a_validation_error(self, authorized_client, signer):
        response = authorized_client.post(URL, json={"declared_type": "ine", "files": []})

        assert response.status_code == 422
        signer.assert_not_called()
