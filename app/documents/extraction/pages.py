"""Page strategy: which pages of a PDF are sent to the provider.

Each type sets ``default_pages`` in its JSON definition: ``"all"`` or ``{"first": n, "last": m}``. Types without it use
``ExtractionConfig.DEFAULT_PAGES``. Uploads have no page-count limit, only the size limit.
"""

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError

from app.config.constants import ExtractionConfig
from app.documents.extraction.base import ExtractionFile
from app.documents.extraction.errors import ExtractionError, InputTooLargeError
from app.documents.registry import get_doc_type_spec

PDF_MIME_TYPE = "application/pdf"


@dataclass(frozen=True)
class PreparedFile:
    """A file ready to be sent. ``pages`` are the 0-based pages kept (``None`` = image or whole PDF)."""

    data: bytes
    mime_type: str
    pages: list[int] | None
    pages_sent: int


def page_strategy(doc_type: str) -> Any:
    """Return the ``default_pages`` of *doc_type*, or the default strategy."""
    spec = get_doc_type_spec(doc_type) or {}
    return spec.get("default_pages", ExtractionConfig.DEFAULT_PAGES)


def select_pages(total: int, strategy: Any) -> list[int]:
    """Return the sorted 0-based pages to keep out of *total* for *strategy*."""
    if strategy == "all":
        return list(range(total))
    if not isinstance(strategy, dict) or not set(strategy) <= {"first", "last"}:
        msg = f"Invalid page strategy: {strategy!r}"
        raise ValueError(msg)
    first = int(strategy.get("first", 0))
    last = int(strategy.get("last", 0))
    if first < 0 or last < 0 or first + last == 0:
        msg = f"Invalid page strategy: {strategy!r}"
        raise ValueError(msg)
    keep = set(range(min(first, total))) | set(range(max(total - last, 0), total))
    return sorted(keep)


def _read_pdf(data: bytes) -> PdfReader:
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            msg = "The PDF is password protected"
            raise ExtractionError(msg)
        _ = len(reader.pages)
    except (PyPdfError, ValueError, KeyError, TypeError) as ex:
        msg = "The PDF cannot be read"
        raise ExtractionError(msg) from ex
    return reader


def prepare_file(file: ExtractionFile, strategy: Any) -> PreparedFile:
    """Apply the page strategy to one file. Images and PDFs that keep every page are sent unchanged."""
    if file.mime_type not in ExtractionConfig.SUPPORTED_MIME_TYPES:
        msg = f"Unsupported content type: {file.mime_type}"
        raise ExtractionError(msg)
    if file.mime_type != PDF_MIME_TYPE:
        return PreparedFile(data=file.data, mime_type=file.mime_type, pages=None, pages_sent=1)

    reader = _read_pdf(file.data)
    total = len(reader.pages)
    if total == 0:
        msg = "The PDF has no pages"
        raise ExtractionError(msg)
    keep = select_pages(total, strategy)
    if len(keep) == total:
        return PreparedFile(data=file.data, mime_type=PDF_MIME_TYPE, pages=None, pages_sent=total)

    writer = PdfWriter()
    for index in keep:
        writer.add_page(reader.pages[index])
    out = BytesIO()
    writer.write(out)
    return PreparedFile(data=out.getvalue(), mime_type=PDF_MIME_TYPE, pages=keep, pages_sent=len(keep))


def prepare_files(files: list[ExtractionFile], doc_type: str) -> list[PreparedFile]:
    """Apply the page strategy of *doc_type* to every file and check the inline request limit."""
    strategy = page_strategy(doc_type)
    prepared = [prepare_file(file, strategy) for file in files]
    total_bytes = sum(len(p.data) for p in prepared)
    if total_bytes > ExtractionConfig.INLINE_REQUEST_MAX_BYTES:
        msg = f"The files add up to {total_bytes} bytes, over the inline limit of the provider"
        raise InputTooLargeError(msg)
    return prepared
