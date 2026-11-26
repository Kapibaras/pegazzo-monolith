from fastapi import HTTPException


class PegazzoException(HTTPException):
    """Base exception for all Pegazzo API errors.

    All domain-specific exceptions should extend this class.
    Guarantees every error response has the shape: { "detail": "..." }. When the exception sets a stable,
    machine-readable ``code`` (e.g. ``file_too_large``), the response also includes it: { "detail": "...", "code": "..." }.
    """

    def __init__(self, status_code: int, detail: str, code: str | None = None, headers: dict[str, str] | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code
