from typing import ClassVar


class DocumentConfig:
    """Document-related configuration constants."""

    EXPIRING_SOON_DAYS = 30
    # Max size of one uploaded document file, same limit as the frontend and AI_MAX_DOCUMENT_BYTES. Shared with PGZ-187.
    # Note: covers ~5 scanned pages (up to ~2.9 MB/page seen in the PoC); revisit with real multi-page scans.
    MAX_FILE_BYTES = 15 * 1024 * 1024
    # Lifetime of presigned PUT/GET URLs, in seconds.
    PRESIGNED_URL_EXPIRES_SECONDS = 3600
    # Not consumed analyses (and their temporary files) older than this are removed by the cleanup task.
    ANALYSIS_RETENTION_HOURS = 24


class ExtractionConfig:
    """Gemini extraction service configuration (PGZ-164). Model, key and timeout live in ``AI`` (env)."""

    # TODO: confirm against Google's current price list (ai.google.dev/gemini-api/docs/pricing). Values used in the
    # PoC for Gemini 3.6 Flash, paid tier, USD per 1M tokens; output includes the thinking tokens.
    # Each entry: (last day the price applies, input price, output price); None = open ended.
    GEMINI_PRICES = (
        ("2026-12-31", 0.75, 3.75),
        (None, 1.50, 7.50),
    )
    # Gemini 3.x thinks before answering and those tokens count inside this cap; a low cap truncates the JSON.
    MAX_OUTPUT_TOKENS = 8192
    # Inline request limit of the Gemini API: 100 MB per request, 50 MB for PDFs (file input methods docs). Older
    # pages still say 20 MB, so verify in staging. Files are always sent inline (no Files API).
    INLINE_REQUEST_MAX_BYTES = 50 * 1024 * 1024
    # Pages sent when a type has no ``default_pages`` in its JSON definition.
    DEFAULT_PAGES: ClassVar[dict[str, int]] = {"first": 3}
    SUPPORTED_MIME_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/webp"})


class GuarantorConfig:
    """Guarantor-related configuration constants."""

    MAX_PER_DRIVER = 5


class AppConfig:
    """Application configuration constants."""

    NAME = "Pegazzo Drivers API"
    VERSION = "0.0.1"
    DESCRIPTION = "API para gestión de conductores y tickets"
