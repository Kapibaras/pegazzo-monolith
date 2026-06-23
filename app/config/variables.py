import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def _require_env(key: str, fallback: str | None = None) -> str:
    value = os.getenv(key, fallback if ENVIRONMENT == "LOCAL" else None)
    if not value:
        raise ValueError(f"{key} environment variable is required")
    return value


DATABASE_URL = _require_env("DATABASE_URL", "sqlite:///./dev.db")
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
]


class AUTHORIZATION:
    """Authorization configuration."""

    JWT_SECRET_KEY: str = _require_env("JWT_SECRET_KEY", "top_secret")
    JWT_ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
