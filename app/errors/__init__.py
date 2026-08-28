from fastapi import HTTPException


class PegazzoException(HTTPException):
    """Base exception for all Pegazzo API errors.

    All domain-specific exceptions should extend this class.
    Guarantees every error response has the shape: { "detail": "..." }.
    """

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
