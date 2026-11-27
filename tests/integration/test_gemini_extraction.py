"""Opt-in integration test against the real Gemini API (skipped by default, never runs in CI).

Run it with a real key and a sample document (values are not printed):

    RUN_GEMINI_INTEGRATION=1 GEMINI_SAMPLE_TYPE=ine GEMINI_SAMPLE_FILES="front.jpg;back.jpg" \
        pipenv run pytest tests/integration -q --no-cov
"""

import asyncio
import mimetypes
import os
from pathlib import Path

import pytest

from app.config import AI
from app.documents.extraction import ExtractionFile, ExtractionOptions, GeminiExtractor
from app.documents.registry import get_doc_type_spec
from app.enum.document import ExpirySource

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_GEMINI_INTEGRATION") != "1" or not AI.GOOGLE_API_KEY,
    reason="Set RUN_GEMINI_INTEGRATION=1 and GOOGLE_API_KEY to call the real Gemini API",
)


def _sample_files() -> list[ExtractionFile]:
    paths = [Path(p) for p in os.getenv("GEMINI_SAMPLE_FILES", "").split(";") if p]
    if not paths:
        pytest.skip("Set GEMINI_SAMPLE_FILES to one or more sample documents (separated by ';')")
    return [ExtractionFile(p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/pdf") for p in paths]


def test_real_extraction():
    declared_type = os.getenv("GEMINI_SAMPLE_TYPE", "ine")
    files = _sample_files()

    result = asyncio.run(
        GeminiExtractor().extract(files, declared_type, ExtractionOptions(analysis_id="integration-test")),
    )

    assert set(result.fields) == set(get_doc_type_spec(declared_type)["fields"])
    assert result.detected_type
    assert isinstance(result.expiry_source, ExpirySource)
    assert result.input_tokens > 0
    assert result.output_tokens > 0
    assert result.pages_sent >= len(files)
