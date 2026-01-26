import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")


class AUTHORIZATION:
    """Authorization configuration."""

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "top_secret")
    JWT_ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
