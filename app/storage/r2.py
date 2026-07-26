import boto3
from botocore.config import Config

from app.config.variables import R2


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=R2.ENDPOINT,
        aws_access_key_id=R2.ACCESS_KEY_ID,
        aws_secret_access_key=R2.SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def generate_document_upload_url(key: str, content_type: str, expires_in: int = 3600) -> str:
    """Generate a presigned PUT URL to upload a private document."""
    client = _get_client()
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2.DOCUMENTS_BUCKET,
            "Key": f"private/{key}",
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def generate_document_read_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned GET URL to temporarily read a private document."""
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": R2.DOCUMENTS_BUCKET,
            "Key": f"private/{key}",
        },
        ExpiresIn=expires_in,
    )


def generate_image_upload_url(key: str, content_type: str, expires_in: int = 3600) -> str:
    """Generate a presigned PUT URL to upload an image to the public bucket."""
    client = _get_client()
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2.IMAGES_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def get_image_public_url(key: str) -> str:
    """Return the public URL for an image stored in the public bucket."""
    return f"{R2.PUBLIC_URL.rstrip('/')}/{key}"


def upload_image(key: str, data: bytes, content_type: str) -> str:
    """Upload an image to the public bucket and return its public URL."""
    client = _get_client()
    client.put_object(
        Bucket=R2.IMAGES_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return get_image_public_url(key)
