import asyncio
import json
import logging
from datetime import date
from unittest.mock import patch

import httpx
import pytest
from google.genai import errors as genai_errors
from google.genai import types

from app.config import AI
from app.documents.extraction import get_document_extractor
from app.documents.extraction.base import ExtractionFile, ExtractionOptions
from app.documents.extraction.errors import ExtractionError, ProviderUnavailableError
from app.documents.extraction.gemini import GeminiExtractor, build_response_schema, estimate_cost, parse_output
from app.enum.document import ExpirySource

INE_FIELDS = {"full_name": "JUAN PEREZ LOPEZ", "curp": "PELJ800101HNLRPN09", "expiry_year": "2033"}
INE_OUTPUT = {
    "detected_type": "ine",
    "issuing_state": "NUEVO LEON",
    "expiry_source": "printed",
    "fields": INE_FIELDS,
}


def _extract(extractor, files, declared_type="ine", options=None):
    return asyncio.run(extractor.extract(files, declared_type, options))


def _call_kwargs(genai_client):
    return genai_client.aio.models.generate_content.call_args.kwargs


class TestExtract:
    """Successful extraction."""

    def test_returns_the_parsed_result(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)

        result = _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        assert result.detected_type == "ine"
        assert result.issuing_state == "NUEVO LEON"
        assert result.expiry_source == ExpirySource.PRINTED
        assert result.fields["curp"] == "PELJ800101HNLRPN09"
        assert result.fields["gender"] is None
        assert result.model_version == "gemini-3.6-flash-001"
        assert result.pages_sent == 1
        assert result.duration_ms >= 0

    def test_ine_front_and_back_go_in_one_call(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)

        result = _extract(extractor, [ExtractionFile(jpeg, "image/jpeg"), ExtractionFile(jpeg + b"2", "image/png")])

        contents = _call_kwargs(genai_client)["contents"]
        assert genai_client.aio.models.generate_content.await_count == 1
        assert len(contents) == 3
        assert "The 2 attached files are parts of the same document" in contents[0]
        assert [part.inline_data.mime_type for part in contents[1:]] == ["image/jpeg", "image/png"]
        assert result.pages_sent == 2

    def test_pdf_pages_follow_the_strategy(self, extractor, genai_client, response_factory, pdf_factory):
        genai_client.aio.models.generate_content.return_value = response_factory(
            {"detected_type": "insurance_policy", "issuing_state": None, "expiry_source": "printed", "fields": {}},
        )

        result = _extract(extractor, [ExtractionFile(pdf_factory(6), "application/pdf")], "insurance_policy")

        assert result.pages_sent == 2
        assert result.pages == [[0, 1]]

    def test_request_config(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)

        _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        kwargs = _call_kwargs(genai_client)
        config = kwargs["config"]
        assert kwargs["model"] == "gemini-3.6-flash"
        assert config.response_mime_type == "application/json"
        assert config.response_schema == build_response_schema("ine")
        assert config.temperature == 0
        assert config.media_resolution is None
        assert config.thinking_config is None

    def test_media_resolution_and_thinking_options(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)

        _extract(
            extractor,
            [ExtractionFile(jpeg, "image/jpeg")],
            options=ExtractionOptions(media_resolution="high", thinking_level="low"),
        )

        config = _call_kwargs(genai_client)["config"]
        assert config.media_resolution == types.MediaResolution.MEDIA_RESOLUTION_HIGH
        assert config.thinking_config.thinking_level == types.ThinkingLevel.LOW

    def test_detected_type_different_from_declared_is_returned(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(
            {**INE_OUTPUT, "detected_type": "driver_license"},
        )

        result = _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        assert result.detected_type == "driver_license"

    def test_tokens_and_cost(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(
            INE_OUTPUT,
            prompt_tokens=2000,
            output_tokens=150,
            thought_tokens=350,
        )

        result = _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        assert result.input_tokens == 2000
        assert result.output_tokens == 500
        assert result.estimated_cost == estimate_cost(2000, 500)

    def test_no_files(self, extractor):
        with pytest.raises(ExtractionError, match="No files"):
            _extract(extractor, [])

    def test_type_without_definition_does_not_call_the_provider(self, extractor, genai_client, jpeg):
        with pytest.raises(ExtractionError, match="no extraction definition"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")], "plates")

        genai_client.aio.models.generate_content.assert_not_awaited()


class TestParseOutput:
    """Response parsing."""

    def test_missing_fields_are_none_and_unknown_keys_dropped(self):
        text = json.dumps({**INE_OUTPUT, "fields": {"curp": " X ", "invented": "1", "address": ""}})

        _, _, _, fields = parse_output(text, "ine")

        assert fields["curp"] == "X"
        assert fields["address"] is None
        assert fields["full_name"] is None
        assert "invented" not in fields

    def test_non_string_values(self):
        text = json.dumps({**INE_OUTPUT, "fields": {"expiry_year": 2033, "address": {"street": "x"}}})

        _, _, _, fields = parse_output(text, "ine")

        assert fields["expiry_year"] == "2033"
        assert fields["address"] is None

    def test_detected_type_outside_taxonomy_is_unknown(self):
        detected, *_ = parse_output(json.dumps({**INE_OUTPUT, "detected_type": "passport"}), "ine")

        assert detected == "unknown"

    def test_unknown_result(self):
        detected, state, source, fields = parse_output(
            json.dumps({"detected_type": "unknown", "issuing_state": None, "expiry_source": "none", "fields": {}}),
            "invoice",
        )

        assert detected == "unknown"
        assert state is None
        assert source == ExpirySource.NONE
        assert set(fields.values()) == {None}

    def test_invalid_expiry_source_is_none(self):
        _, _, source, _ = parse_output(json.dumps({**INE_OUTPUT, "expiry_source": "guess"}), "ine")

        assert source == ExpirySource.NONE

    @pytest.mark.parametrize("text", ["not json", "", "[1, 2]", '"text"'])
    def test_invalid_output(self, text):
        with pytest.raises(ExtractionError):
            parse_output(text, "ine")


class TestResponseErrors:
    """Unusable responses are not retryable."""

    def test_invalid_json(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory("{not json")

        with pytest.raises(ExtractionError, match="invalid JSON"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

    def test_truncated(self, extractor, genai_client, response_factory, jpeg):
        genai_client.aio.models.generate_content.return_value = response_factory(
            INE_OUTPUT,
            finish=types.FinishReason.MAX_TOKENS,
        )

        with pytest.raises(ExtractionError, match="truncated"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

    def test_no_candidates(self, extractor, genai_client, jpeg):
        genai_client.aio.models.generate_content.return_value = types.GenerateContentResponse(candidates=[])

        with pytest.raises(ExtractionError, match="no candidates"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

    def test_blocked(self, extractor, genai_client, jpeg):
        genai_client.aio.models.generate_content.return_value = types.GenerateContentResponse(
            prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=types.BlockedReason.SAFETY),
        )

        with pytest.raises(ExtractionError, match="blocked"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])


class TestErrorMapping:
    """Provider errors: 503 / 429 / 5xx / timeouts are retryable, other 4xx are not."""

    @pytest.mark.parametrize(
        "error",
        [
            genai_errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}),
            genai_errors.ServerError(500, {"error": {"code": 500, "message": "internal", "status": "INTERNAL"}}),
            genai_errors.ClientError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}}),
        ],
    )
    def test_retryable_status(self, extractor, genai_client, jpeg, error):
        genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(ProviderUnavailableError) as exc_info:
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        assert exc_info.value.status_code == error.code

    @pytest.mark.parametrize(
        "error",
        [TimeoutError(), httpx.ReadTimeout("read timeout"), httpx.ConnectError("connection refused")],
    )
    def test_timeouts_and_connection_errors(self, extractor, genai_client, jpeg, error):
        genai_client.aio.models.generate_content.side_effect = error

        with pytest.raises(ProviderUnavailableError):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

    def test_slow_call_hits_the_timeout(self, genai_client, jpeg):
        async def slow(**_kwargs):
            await asyncio.sleep(1)

        genai_client.aio.models.generate_content.side_effect = slow
        extractor = GeminiExtractor(client=genai_client, timeout_seconds=0.01)

        with pytest.raises(ProviderUnavailableError, match="timeout"):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

    @pytest.mark.parametrize("code", [400, 403, 404])
    def test_other_client_errors(self, extractor, genai_client, jpeg, code):
        genai_client.aio.models.generate_content.side_effect = genai_errors.ClientError(
            code,
            {"error": {"code": code, "message": "bad request", "status": "INVALID_ARGUMENT"}},
        )

        with pytest.raises(ExtractionError) as exc_info:
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        assert exc_info.value.status_code == code
        assert not isinstance(exc_info.value, ProviderUnavailableError)


class TestCallLog:
    """One structured line per provider call, without extracted values or file contents."""

    @staticmethod
    def _entries(caplog):
        return [
            json.loads(r.getMessage().removeprefix("document_extraction_call "))
            for r in caplog.records
            if r.getMessage().startswith("document_extraction_call ")
        ]

    def test_success_line(self, extractor, genai_client, response_factory, jpeg, caplog):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)
        caplog.set_level(logging.INFO)

        _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")], options=ExtractionOptions(analysis_id="a-1", attempt=2))

        [entry] = self._entries(caplog)
        assert entry["analysis_id"] == "a-1"
        assert entry["attempt"] == 2
        assert entry["declared_type"] == "ine"
        assert entry["detected_type"] == "ine"
        assert entry["pages_sent"] == 1
        assert entry["model"] == "gemini-3.6-flash"
        assert entry["input_tokens"] == 1000
        assert entry["output_tokens"] == 500
        assert entry["estimated_cost"] == estimate_cost(1000, 500)
        assert entry["outcome"] == "ok"
        assert "duration_ms" in entry

    def test_never_logs_values_or_contents(self, extractor, genai_client, response_factory, jpeg, caplog):
        genai_client.aio.models.generate_content.return_value = response_factory(INE_OUTPUT)
        caplog.set_level(logging.DEBUG)

        _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        for value in [*INE_FIELDS.values(), "NUEVO LEON", jpeg.decode("latin-1")]:
            assert value not in caplog.text

    def test_error_line(self, extractor, genai_client, jpeg, caplog):
        genai_client.aio.models.generate_content.side_effect = genai_errors.ServerError(
            503,
            {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}},
        )
        caplog.set_level(logging.INFO)

        with pytest.raises(ProviderUnavailableError):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        [entry] = self._entries(caplog)
        assert entry["outcome"] == "provider_unavailable"
        assert entry["status_code"] == 503

    def test_unparsable_output_line(self, extractor, genai_client, response_factory, jpeg, caplog):
        genai_client.aio.models.generate_content.return_value = response_factory("nope")
        caplog.set_level(logging.INFO)

        with pytest.raises(ExtractionError):
            _extract(extractor, [ExtractionFile(jpeg, "image/jpeg")])

        [entry] = self._entries(caplog)
        assert entry["outcome"] == "extraction_error"
        assert entry["input_tokens"] == 1000


class TestCost:
    """Estimated cost from the configured per-token prices."""

    def test_current_price(self):
        assert estimate_cost(1_000_000, 1_000_000, today=date(2026, 12, 31)) == pytest.approx(0.75 + 3.75)

    def test_price_after_the_change(self):
        assert estimate_cost(1_000_000, 1_000_000, today=date(2027, 1, 1)) == pytest.approx(1.50 + 7.50)

    def test_typical_document(self):
        assert estimate_cost(2500, 1500, today=date(2026, 11, 27)) == pytest.approx(0.0075)


class TestClient:
    """SDK client creation."""

    def test_requires_the_key(self, jpeg):
        with patch.object(AI, "GOOGLE_API_KEY", ""), pytest.raises(ExtractionError, match="GOOGLE_API_KEY"):
            _extract(GeminiExtractor(), [ExtractionFile(jpeg, "image/jpeg")])

    def test_uses_the_key_and_timeout(self):
        with (
            patch.object(AI, "GOOGLE_API_KEY", "test-key"),
            patch("app.documents.extraction.gemini.genai.Client") as client_cls,
        ):
            extractor = GeminiExtractor(timeout_seconds=20)
            assert extractor.client is client_cls.return_value
            assert extractor.client is client_cls.return_value

        client_cls.assert_called_once()
        kwargs = client_cls.call_args.kwargs
        assert kwargs["api_key"] == "test-key"
        assert kwargs["http_options"].timeout == 20000

    def test_shared_extractor(self):
        assert get_document_extractor() is get_document_extractor()
        assert isinstance(get_document_extractor(), GeminiExtractor)
