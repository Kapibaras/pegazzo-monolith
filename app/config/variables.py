import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL").upper()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def _require_env(key: str, fallback: str | None = None) -> str:
    value = os.getenv(key)
    if value:
        return value
    if ENVIRONMENT == "LOCAL" and fallback is not None:
        return fallback
    raise ValueError(f"{key} environment variable is required")


DATABASE_URL = _require_env("DATABASE_URL", "sqlite:///./dev.db")
CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]


DOCS_USER: str = os.getenv("DOCS_USER", "")
DOCS_PASSWORD: str = os.getenv("DOCS_PASSWORD", "")


class R2:
    """Cloudflare R2 object storage configuration.

    Uses os.getenv instead of _require_env so that services which never
    touch R2 (e.g. Celery beat) can start without these variables.
    Actual validation happens at the point of use (R2 storage client).
    """

    ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    ENDPOINT: str = os.getenv("R2_ENDPOINT", "")
    DOCUMENTS_BUCKET: str = os.getenv("R2_DOCUMENTS_BUCKET", "pegazzo-documents")
    IMAGES_BUCKET: str = os.getenv("R2_IMAGES_BUCKET", "pegazzo-images")
    PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")


class CELERY:
    """Celery task queue configuration."""

    BROKER_URL: str = _require_env("CELERY_BROKER_URL", "redis://localhost:6379/0")
    RESULT_BACKEND: str = _require_env("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
    WORKER_STUCK_TASK_MINUTES: int = int(os.getenv("WORKER_STUCK_TASK_MINUTES", "10"))


class AUTHORIZATION:
    """Authorization configuration."""

    JWT_SECRET_KEY: str = _require_env("JWT_SECRET_KEY", "top_secret")
    JWT_ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
