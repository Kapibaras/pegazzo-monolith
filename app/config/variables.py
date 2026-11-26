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


class AI:
    """AI document analysis provider (Gemini) configuration.

    Uses os.getenv instead of _require_env so that services which import
    app.config but never call the provider (Celery worker/beat) can start
    without GOOGLE_API_KEY. The API validates these values at startup via
    AI.validate(); the key must only be configured on the API service.
    """

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    GEMINI_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "15"))
    # TODO(PGZ-187): final limit is defined there. 15 MB matches the frontend and the upload limit (PGZ-179);
    # it covers ~5 scanned pages, revisit with real multi-page scans.
    MAX_DOCUMENT_BYTES: int = int(os.getenv("AI_MAX_DOCUMENT_BYTES", "15728640"))
    RETRY_BUDGET_SECONDS: float = float(os.getenv("AI_RETRY_BUDGET_SECONDS", "20"))

    @classmethod
    def validate(cls) -> None:
        """Fail fast on missing key (outside LOCAL) or inconsistent limits. Never includes the key in errors."""
        _require_env("GOOGLE_API_KEY", "")
        if cls.GEMINI_TIMEOUT_SECONDS <= 0:
            raise ValueError(f"GEMINI_TIMEOUT_SECONDS must be > 0 (got {cls.GEMINI_TIMEOUT_SECONDS})")
        if cls.RETRY_BUDGET_SECONDS < cls.GEMINI_TIMEOUT_SECONDS:
            raise ValueError(
                f"AI_RETRY_BUDGET_SECONDS ({cls.RETRY_BUDGET_SECONDS}) must be >= "
                f"GEMINI_TIMEOUT_SECONDS ({cls.GEMINI_TIMEOUT_SECONDS})",
            )
        if cls.MAX_DOCUMENT_BYTES <= 0:
            raise ValueError(f"AI_MAX_DOCUMENT_BYTES must be > 0 (got {cls.MAX_DOCUMENT_BYTES})")


class AUTHORIZATION:
    """Authorization configuration."""

    JWT_SECRET_KEY: str = _require_env("JWT_SECRET_KEY", "top_secret")
    JWT_ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
