import os

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "LOCAL")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "top_secret")
JWT_ACCESS_TOKEN_EXPIRES_MIN = os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", "15")
JWT_REFRESH_TOKEN_EXPIRES_DAYS = os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7")
