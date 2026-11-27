import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai import types
from pypdf import PdfWriter

from app.documents.extraction.gemini import GeminiExtractor

JPEG = b"\xff\xd8\xff\xe0 fake jpeg bytes"


def make_pdf(pages: int) -> bytes:
    """Build a PDF with *pages* blank pages."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def make_response(
    payload: dict | str,
    *,
    finish: types.FinishReason = types.FinishReason.STOP,
    prompt_tokens: int = 1000,
    output_tokens: int = 200,
    thought_tokens: int = 300,
) -> types.GenerateContentResponse:
    """Build a real SDK response with *payload* as the JSON text."""
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]), finish_reason=finish)],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt_tokens,
            candidates_token_count=output_tokens,
            thoughts_token_count=thought_tokens,
        ),
        model_version="gemini-3.6-flash-001",
    )


@pytest.fixture
def genai_client():
    """Fake SDK client: ``client.aio.models.generate_content`` is an AsyncMock."""
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock()
    return client


@pytest.fixture
def extractor(genai_client):
    return GeminiExtractor(client=genai_client, model="gemini-3.6-flash", timeout_seconds=5)


@pytest.fixture
def pdf_factory():
    return make_pdf


@pytest.fixture
def response_factory():
    return make_response


@pytest.fixture
def jpeg():
    return JPEG
