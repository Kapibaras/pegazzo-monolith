from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.storage.r2 import (
    StoredObject,
    copy_document,
    delete_document,
    delete_documents_best_effort,
    download_document,
    generate_document_upload_url,
    head_document,
)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "HeadObject")


@pytest.fixture
def r2_client():
    with patch("app.storage.r2.boto3.client") as mock_boto_client:
        client = MagicMock()
        mock_boto_client.return_value = client
        yield client


class TestUploadUrlContentLength:
    """The presigned PUT signs the content length when given."""

    def test_content_length_is_signed(self, r2_client):
        generate_document_upload_url("tmp/analysis/a/0.jpg", "image/jpeg", content_length=2400000)

        params = r2_client.generate_presigned_url.call_args[1]["Params"]
        assert params["ContentLength"] == 2400000
        assert params["Key"] == "private/tmp/analysis/a/0.jpg"
        assert params["ContentType"] == "image/jpeg"

    def test_content_length_omitted_by_default(self, r2_client):
        generate_document_upload_url("car/X/doc.pdf", "application/pdf")

        assert "ContentLength" not in r2_client.generate_presigned_url.call_args[1]["Params"]


class TestHeadDocument:
    """head_document returns metadata or None."""

    def test_returns_size_and_content_type(self, r2_client):
        r2_client.head_object.return_value = {"ContentLength": 123, "ContentType": "image/png"}

        assert head_document("tmp/analysis/a/0.png") == StoredObject(size=123, content_type="image/png")
        assert r2_client.head_object.call_args[1]["Key"] == "private/tmp/analysis/a/0.png"

    @pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
    def test_returns_none_when_missing(self, r2_client, code):
        r2_client.head_object.side_effect = _client_error(code)

        assert head_document("tmp/analysis/a/0.png") is None

    def test_raises_other_errors(self, r2_client):
        r2_client.head_object.side_effect = _client_error("403")

        with pytest.raises(ClientError):
            head_document("tmp/analysis/a/0.png")


class TestDocumentObjects:
    """download, copy and delete of private documents."""

    def test_download_document(self, r2_client):
        body = MagicMock()
        body.read.return_value = b"data"
        r2_client.get_object.return_value = {"Body": body}

        assert download_document("tmp/analysis/a/0.pdf") == b"data"
        assert r2_client.get_object.call_args[1]["Key"] == "private/tmp/analysis/a/0.pdf"

    def test_copy_document_adds_private_prefix(self, r2_client):
        copy_document("tmp/analysis/a/0.pdf", "car/X/uuid.pdf")

        kwargs = r2_client.copy_object.call_args[1]
        assert kwargs["Key"] == "private/car/X/uuid.pdf"
        assert kwargs["CopySource"]["Key"] == "private/tmp/analysis/a/0.pdf"
        assert kwargs["CopySource"]["Bucket"] == kwargs["Bucket"]

    def test_delete_document(self, r2_client):
        delete_document("tmp/analysis/a/0.pdf")

        assert r2_client.delete_object.call_args[1]["Key"] == "private/tmp/analysis/a/0.pdf"

    def test_delete_documents_best_effort_continues_on_error(self, r2_client):
        r2_client.delete_object.side_effect = [RuntimeError("boom"), None]

        delete_documents_best_effort(["a", "b"])

        assert r2_client.delete_object.call_count == 2
