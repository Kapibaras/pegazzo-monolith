"""Gemini implementation of ``DocumentExtractor`` (official ``google-genai`` SDK, async client).

Files are always sent inline as bytes (``Part.from_bytes``); nothing is uploaded to the Files API. The SDK runs with
its default "never retry" policy: retries belong to the analysis endpoint (PGZ-124).
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import cache
from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import AI
from app.config.constants import ExtractionConfig
from app.documents.extraction.base import ExtractionFile, ExtractionOptions, ExtractionResult
from app.documents.extraction.errors import ExtractionError, ProviderUnavailableError
from app.documents.extraction.pages import prepare_files
from app.documents.extraction.prompt import UNKNOWN_TYPE, build_prompt, extraction_spec, taxonomy
from app.enum.document import ExpirySource
from app.utils.logging_config import logger

RETRYABLE_STATUS = frozenset({408, 429})
COMMON_KEYS = ("detected_type", "issuing_state", "expiry_source", "fields", "unreadable_fields")


@dataclass(frozen=True)
class ParsedOutput:
    """Model output after validation against the declared type."""

    detected_type: str
    issuing_state: str | None
    expiry_source: ExpirySource
    fields: dict[str, str | None]
    unreadable_fields: list[str]


def estimate_cost(input_tokens: int, output_tokens: int, today: date | None = None) -> float:
    """Return the estimated USD cost of one call with the configured per-token prices."""
    today = today or datetime.now(UTC).date()
    for until, input_price, output_price in ExtractionConfig.GEMINI_PRICES:
        if until is None or today <= date.fromisoformat(until):
            return round(input_tokens / 1_000_000 * input_price + output_tokens / 1_000_000 * output_price, 6)
    return 0.0


def build_response_schema(declared_type: str) -> types.Schema:
    """Response schema: common keys plus every field of the declared type as a nullable string."""
    spec = extraction_spec(declared_type)
    names = list(spec["fields"])
    fields = types.Schema(
        type=types.Type.OBJECT,
        properties={name: types.Schema(type=types.Type.STRING, nullable=True) for name in names},
        required=names,
        property_ordering=names,
    )
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "detected_type": types.Schema(type=types.Type.STRING, enum=taxonomy()),
            "issuing_state": types.Schema(type=types.Type.STRING, nullable=True),
            "expiry_source": types.Schema(type=types.Type.STRING, enum=[e.value for e in ExpirySource]),
            "fields": fields,
            "unreadable_fields": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING, enum=names),
            ),
        },
        required=[*COMMON_KEYS],
        property_ordering=[*COMMON_KEYS],
    )


def _clean(value: Any) -> str | None:
    if value is None or isinstance(value, dict | list):
        return None
    text = str(value).strip()
    return text or None


def parse_output(text: str, declared_type: str) -> ParsedOutput:
    """Parse and validate the model output.

    Missing fields become ``None`` and unknown keys are dropped. ``unreadable_fields`` keeps only known field names and
    their values are forced to ``None`` (printed but not legible is never guessed). Raises ``ExtractionError`` when the
    output is not a JSON object.
    """
    try:
        data = json.loads(text)
    except (TypeError, ValueError) as ex:
        msg = "The provider returned invalid JSON"
        raise ExtractionError(msg) from ex
    if not isinstance(data, dict):
        msg = "The provider did not return a JSON object"
        raise ExtractionError(msg)

    raw_fields = data.get("fields")
    raw_fields = raw_fields if isinstance(raw_fields, dict) else {}
    names = extraction_spec(declared_type)["fields"]
    fields = {name: _clean(raw_fields.get(name)) for name in names}
    raw_unreadable = data.get("unreadable_fields")
    raw_unreadable = raw_unreadable if isinstance(raw_unreadable, list) else []
    unreadable = list(dict.fromkeys(name for name in raw_unreadable if name in names))
    for name in unreadable:
        fields[name] = None

    detected = _clean(data.get("detected_type"))
    detected = detected if detected in taxonomy() else UNKNOWN_TYPE
    source = _clean(data.get("expiry_source"))
    expiry_source = ExpirySource(source) if source in {e.value for e in ExpirySource} else ExpirySource.NONE
    return ParsedOutput(
        detected_type=detected,
        issuing_state=_clean(data.get("issuing_state")),
        expiry_source=expiry_source,
        fields=fields,
        unreadable_fields=unreadable,
    )


def _map_api_error(ex: genai_errors.APIError) -> Exception:
    code = ex.code
    if code in RETRYABLE_STATUS or (code is not None and code >= 500):
        return ProviderUnavailableError(f"Provider unavailable ({code})", status_code=code)
    return ExtractionError(f"Provider rejected the request ({code})", status_code=code)


class GeminiExtractor:
    """Extract one analysis with Gemini. The SDK client is created on first use (the key is only needed then)."""

    def __init__(self, client: Any = None, model: str | None = None, timeout_seconds: float | None = None):
        self._client = client
        self.model = model or AI.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds or AI.GEMINI_TIMEOUT_SECONDS

    @property
    def client(self) -> Any:
        """Return the SDK client, creating it with the configured key and timeout on first use."""
        if self._client is None:
            if not AI.GOOGLE_API_KEY:
                msg = "GOOGLE_API_KEY is not configured"
                raise ExtractionError(msg)
            self._client = genai.Client(
                api_key=AI.GOOGLE_API_KEY,
                http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
            )
        return self._client

    def _config(self, declared_type: str, options: ExtractionOptions) -> types.GenerateContentConfig:
        extra: dict[str, Any] = {}
        if options.thinking_level:
            extra["thinking_config"] = types.ThinkingConfig(thinking_level=options.thinking_level.upper())
        if options.media_resolution:
            extra["media_resolution"] = types.MediaResolution[f"MEDIA_RESOLUTION_{options.media_resolution.upper()}"]
        return types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=ExtractionConfig.MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",
            response_schema=build_response_schema(declared_type),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            **extra,
        )

    async def _generate(self, contents: list[Any], config: types.GenerateContentConfig) -> Any:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                return await self.client.aio.models.generate_content(model=self.model, contents=contents, config=config)
        except genai_errors.APIError as ex:
            raise _map_api_error(ex) from ex
        except (TimeoutError, httpx.TimeoutException) as ex:
            msg = "Provider timeout"
            raise ProviderUnavailableError(msg) from ex
        except httpx.TransportError as ex:
            msg = "Provider connection error"
            raise ProviderUnavailableError(msg) from ex

    @staticmethod
    def _response_text(response: Any) -> str:
        feedback = getattr(response, "prompt_feedback", None)
        if feedback is not None and getattr(feedback, "block_reason", None):
            msg = "The provider blocked the request"
            raise ExtractionError(msg)
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            msg = "The provider returned no candidates"
            raise ExtractionError(msg)
        finish = getattr(getattr(candidates[0], "finish_reason", None), "name", None)
        if finish == "MAX_TOKENS":
            msg = "The provider output was truncated"
            raise ExtractionError(msg)
        return response.text or ""

    async def extract(
        self,
        files: list[ExtractionFile],
        declared_type: str,
        options: ExtractionOptions | None = None,
    ) -> ExtractionResult:
        """Send the files of one analysis in a single call and return the raw extraction."""
        options = options or ExtractionOptions()
        if not files:
            msg = "No files to extract"
            raise ExtractionError(msg)
        extraction_spec(declared_type)
        prepared = await asyncio.to_thread(prepare_files, files, declared_type)
        pages_sent = sum(p.pages_sent for p in prepared)
        log = CallLog(options, declared_type, self.model, len(prepared), pages_sent)

        contents: list[Any] = [build_prompt(declared_type, len(prepared))]
        contents += [types.Part.from_bytes(data=p.data, mime_type=p.mime_type) for p in prepared]
        config = self._config(declared_type, options)

        started = time.monotonic()
        try:
            response = await self._generate(contents, config)
            input_tokens, output_tokens = _usage(response)
            log.tokens(input_tokens, output_tokens)
            text = self._response_text(response)
            parsed = parse_output(text, declared_type)
        except (ExtractionError, ProviderUnavailableError) as ex:
            log.emit(started, ex)
            raise

        duration_ms = log.emit(started, None, parsed)
        return ExtractionResult(
            detected_type=parsed.detected_type,
            issuing_state=parsed.issuing_state,
            expiry_source=parsed.expiry_source,
            fields=parsed.fields,
            unreadable_fields=parsed.unreadable_fields,
            model_version=getattr(response, "model_version", None) or self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimate_cost(input_tokens, output_tokens),
            duration_ms=duration_ms,
            pages_sent=pages_sent,
            pages=[p.pages for p in prepared],
        )


def _usage(response: Any) -> tuple[int, int]:
    """Return ``(input, output)`` tokens; output includes the thinking tokens (billed as output)."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return 0, 0
    output = (getattr(usage, "candidates_token_count", 0) or 0) + (getattr(usage, "thoughts_token_count", 0) or 0)
    return getattr(usage, "prompt_token_count", 0) or 0, output


class CallLog:
    """One structured log line per provider call. Never holds extracted values, file contents, URLs or the key."""

    def __init__(self, options: ExtractionOptions, declared_type: str, model: str, files: int, pages_sent: int):
        self.entry: dict[str, Any] = {
            "analysis_id": options.analysis_id,
            "declared_type": declared_type,
            "files": files,
            "pages_sent": pages_sent,
            "model": model,
            "attempt": options.attempt,
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Record the token usage of the call."""
        self.entry["input_tokens"] = input_tokens
        self.entry["output_tokens"] = output_tokens

    def emit(self, started: float, error: Exception | None, parsed: ParsedOutput | None = None) -> int:
        """Write the log line and return the call duration in milliseconds."""
        duration_ms = int((time.monotonic() - started) * 1000)
        self.entry["duration_ms"] = duration_ms
        self.entry["estimated_cost"] = estimate_cost(self.entry["input_tokens"], self.entry["output_tokens"])
        if error is None:
            self.entry["outcome"] = "ok"
            self.entry["detected_type"] = parsed.detected_type if parsed else None
            # Names only (not personal data): printed fields the model could not read.
            self.entry["unreadable_fields"] = parsed.unreadable_fields if parsed else []
            logger.info("document_extraction_call %s", json.dumps(self.entry))
        else:
            self.entry["outcome"] = (
                "provider_unavailable" if isinstance(error, ProviderUnavailableError) else "extraction_error"
            )
            self.entry["status_code"] = getattr(error, "status_code", None)
            logger.warning("document_extraction_call %s", json.dumps(self.entry))
        return duration_ms


@cache
def get_document_extractor() -> GeminiExtractor:
    """Return the shared extractor used by the analysis pipeline (PGZ-124)."""
    return GeminiExtractor()
