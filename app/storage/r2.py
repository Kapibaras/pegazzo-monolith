from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config.variables import R2
from app.utils.logging_config import logger


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=R2.ENDPOINT,
        aws_access_key_id=R2.ACCESS_KEY_ID,
        aws_secret_access_key=R2.SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


@dataclass(frozen=True)
class StoredObject:
    """Metadata of an object stored in R2."""

    size: int
    content_type: str | None


_NOT_FOUND_CODES = frozenset({"404", "NoSuchKey", "NotFound"})


def generate_document_upload_url(
    key: str,
    content_type: str,
    expires_in: int = 3600,
    content_length: int | None = None,
) -> str:
    """Generate a presigned PUT URL to upload a private document.

    When *content_length* is given it is signed too, so R2 rejects a body of a different size.
    """
    client = _get_client()
    params = {
        "Bucket": R2.DOCUMENTS_BUCKET,
        "Key": f"private/{key}",
        "ContentType": content_type,
    }
    if content_length is not None:
        params["ContentLength"] = content_length
    return client.generate_presigned_url("put_object", Params=params, ExpiresIn=expires_in)


def head_document(key: str) -> StoredObject | None:
    """Return the size and content type of a private document, or ``None`` when it does not exist."""
    client = _get_client()
    try:
        response = client.head_object(Bucket=R2.DOCUMENTS_BUCKET, Key=f"private/{key}")
    except ClientError as ex:
        if ex.response.get("Error", {}).get("Code") in _NOT_FOUND_CODES:
            return None
        raise
    return StoredObject(size=response["ContentLength"], content_type=response.get("ContentType"))


def download_document(key: str) -> bytes:
    """Return the content of a private document."""
    client = _get_client()
    response = client.get_object(Bucket=R2.DOCUMENTS_BUCKET, Key=f"private/{key}")
    return response["Body"].read()


def copy_document(src: str, dst: str) -> None:
    """Copy a private document to another key of the documents bucket (server side, nothing goes through the API)."""
    client = _get_client()
    client.copy_object(
        Bucket=R2.DOCUMENTS_BUCKET,
        Key=f"private/{dst}",
        CopySource={"Bucket": R2.DOCUMENTS_BUCKET, "Key": f"private/{src}"},
    )


def delete_document(key: str) -> None:
    """Permanently delete a private document (temporary files; final documents use ``soft_delete_document``)."""
    client = _get_client()
    client.delete_object(Bucket=R2.DOCUMENTS_BUCKET, Key=f"private/{key}")


def delete_documents_best_effort(keys: list[str]) -> None:
    """Permanently delete each document, logging failures instead of raising."""
    for key in keys:
        try:
            delete_document(key)
        except Exception as ex:  # noqa: BLE001 - cleanup must never fail the caller; the R2 lifecycle rule is the safety net
            logger.error("Storage delete failed for '%s': %s", key, ex, exc_info=True)


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


def soft_delete_object(bucket: str, key: str) -> None:
    """Move an object to the `deleted/` prefix of its bucket instead of removing it."""
    client = _get_client()
    client.copy_object(
        Bucket=bucket,
        Key=f"deleted/{key}",
        CopySource={"Bucket": bucket, "Key": key},
    )
    client.delete_object(Bucket=bucket, Key=key)


def soft_delete_document(key: str) -> None:
    """Move a private document (stored under `private/<key>`) to the `deleted/` prefix."""
    soft_delete_object(R2.DOCUMENTS_BUCKET, f"private/{key}")


def soft_delete_documents_best_effort(keys: list[str]) -> None:
    """Move each document to the `deleted/` prefix, logging failures instead of raising."""
    for key in keys:
        try:
            soft_delete_document(key)
        except Exception as ex:  # noqa: BLE001 - storage cleanup runs after the commit and must not fail the request
            logger.error("Storage cleanup failed for '%s': %s", key, ex, exc_info=True)


def soft_delete_image(url: str) -> bool:
    """Move a public image to the `deleted/` prefix. Return False if the URL is not from our bucket."""
    prefix = f"{R2.PUBLIC_URL.rstrip('/')}/"
    if not url.startswith(prefix):
        return False
    soft_delete_object(R2.IMAGES_BUCKET, url[len(prefix) :])
    return True
