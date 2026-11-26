class DocumentConfig:
    """Document-related configuration constants."""

    EXPIRING_SOON_DAYS = 30
    # Max size of one uploaded document file, same limit as the frontend. Shared with PGZ-187 (upload limits).
    MAX_FILE_BYTES = 15 * 1024 * 1024
    # Lifetime of presigned PUT/GET URLs, in seconds.
    PRESIGNED_URL_EXPIRES_SECONDS = 3600
    # Not consumed analyses (and their temporary files) older than this are removed by the cleanup task.
    ANALYSIS_RETENTION_HOURS = 24


class GuarantorConfig:
    """Guarantor-related configuration constants."""

    MAX_PER_DRIVER = 5


class AppConfig:
    """Application configuration constants."""

    NAME = "Pegazzo Drivers API"
    VERSION = "0.0.1"
    DESCRIPTION = "API para gestión de conductores y tickets"
