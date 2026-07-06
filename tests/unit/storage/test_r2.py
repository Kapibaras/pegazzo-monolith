from unittest.mock import MagicMock, patch

from app.storage.r2 import (
    generate_document_read_url,
    generate_document_upload_url,
    get_image_public_url,
    upload_image,
)


class TestR2Storage:
    """Unit tests for Cloudflare R2 storage client."""

    @patch("app.storage.r2.boto3.client")
    def test_generate_document_upload_url(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://r2.example.com/presigned-put"

        url = generate_document_upload_url("drivers/123/ine.pdf", "application/pdf")

        mock_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": mock_client.generate_presigned_url.call_args[1]["Params"]["Bucket"],
                "Key": "private/drivers/123/ine.pdf",
                "ContentType": "application/pdf",
            },
            ExpiresIn=3600,
        )
        assert url == "https://r2.example.com/presigned-put"

    @patch("app.storage.r2.boto3.client")
    def test_generate_document_upload_url_custom_expiry(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://r2.example.com/presigned-put"

        generate_document_upload_url("cars/abc/poliza.pdf", "application/pdf", expires_in=7200)

        call_kwargs = mock_client.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 7200

    @patch("app.storage.r2.boto3.client")
    def test_generate_document_read_url(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://r2.example.com/presigned-get"

        url = generate_document_read_url("drivers/123/ine.pdf")

        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": mock_client.generate_presigned_url.call_args[1]["Params"]["Bucket"],
                "Key": "private/drivers/123/ine.pdf",
            },
            ExpiresIn=3600,
        )
        assert url == "https://r2.example.com/presigned-get"

    @patch("app.storage.r2.boto3.client")
    def test_generate_document_read_url_custom_expiry(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.generate_presigned_url.return_value = "https://r2.example.com/presigned-get"

        generate_document_read_url("drivers/123/ine.pdf", expires_in=600)

        call_kwargs = mock_client.generate_presigned_url.call_args
        assert call_kwargs[1]["ExpiresIn"] == 600

    @patch("app.storage.r2.R2")
    def test_get_image_public_url(self, mock_r2):
        mock_r2.PUBLIC_URL = "https://pub-abc123.r2.dev"

        url = get_image_public_url("cars/abc/agency.jpg")

        assert url == "https://pub-abc123.r2.dev/cars/abc/agency.jpg"

    @patch("app.storage.r2.R2")
    def test_get_image_public_url_strips_trailing_slash(self, mock_r2):
        mock_r2.PUBLIC_URL = "https://pub-abc123.r2.dev/"

        url = get_image_public_url("drivers/123/photo.jpg")

        assert url == "https://pub-abc123.r2.dev/drivers/123/photo.jpg"

    @patch("app.storage.r2.R2")
    @patch("app.storage.r2.boto3.client")
    def test_upload_image_returns_public_url(self, mock_boto_client, mock_r2):
        mock_r2.PUBLIC_URL = "https://pub-abc123.r2.dev"
        mock_r2.IMAGES_BUCKET = "pegazzo-images"
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        url = upload_image("cars/abc/agency.jpg", b"imagedata", "image/jpeg")

        mock_client.put_object.assert_called_once_with(
            Bucket="pegazzo-images",
            Key="cars/abc/agency.jpg",
            Body=b"imagedata",
            ContentType="image/jpeg",
        )
        assert url == "https://pub-abc123.r2.dev/cars/abc/agency.jpg"
