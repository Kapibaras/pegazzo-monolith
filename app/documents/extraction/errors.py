"""Errors raised by the extraction service.

They are not HTTP errors: the analysis endpoint (PGZ-124) decides what to do with them.
``ProviderUnavailableError`` is retryable (the endpoint retries within its budget; this service never sleeps or
retries); ``ExtractionError`` is not.
"""


class ProviderUnavailableError(Exception):
    """The provider is temporarily unavailable (503, 429, other 5xx, timeout or connection error)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ExtractionError(Exception):
    """The document cannot be extracted (provider 4xx, unparsable output, unsupported input). Not retryable."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class InputTooLargeError(ExtractionError):
    """The files of one analysis exceed the inline request limit of the provider."""
