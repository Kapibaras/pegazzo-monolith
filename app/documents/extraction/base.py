"""Provider-agnostic types of the extraction service: input files, options, result and the extractor protocol."""

from dataclasses import dataclass, field
from typing import Literal, NamedTuple, Protocol

from app.enum.document import ExpirySource

MediaResolution = Literal["low", "medium", "high"]
ThinkingLevel = Literal["minimal", "low", "medium", "high"]


class ExtractionFile(NamedTuple):
    """One file of an analysis, already downloaded (and normalized by the quality gate, PGZ-165)."""

    data: bytes
    mime_type: str


@dataclass(frozen=True)
class ExtractionOptions:
    """Per-call options. ``analysis_id`` and ``attempt`` only go to the call log."""

    analysis_id: str | None = None
    attempt: int = 1
    media_resolution: MediaResolution | None = None
    thinking_level: ThinkingLevel | None = None


@dataclass(frozen=True)
class ExtractionResult:
    """Raw extraction of one analysis. ``fields`` holds the values exactly as read (strings or ``None``)."""

    detected_type: str
    issuing_state: str | None
    expiry_source: ExpirySource
    fields: dict[str, str | None]
    model_version: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    duration_ms: int
    pages_sent: int
    # Per file: page indexes sent (0-based), ``None`` for images or a whole PDF.
    pages: list[list[int] | None] = field(default_factory=list)


class DocumentExtractor(Protocol):
    """Reads the files of one analysis and returns the detected type and the raw fields of the declared type."""

    async def extract(
        self,
        files: list[ExtractionFile],
        declared_type: str,
        options: ExtractionOptions | None = None,
    ) -> ExtractionResult:
        """Extract one document made of 1..N files (e.g. INE front and back)."""
        ...
