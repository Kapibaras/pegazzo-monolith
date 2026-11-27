import pytest

from app.documents.extraction.errors import ExtractionError
from app.documents.extraction.prompt import build_prompt, extraction_spec, taxonomy
from app.documents.registry import get_doc_type_spec

PORTED_TYPES = ["ine", "circulation_card", "insurance_policy", "invoice", "invoice_letter", "tax_status_certificate"]


class TestBuildPrompt:
    """Prompt assembly per type."""

    @pytest.mark.parametrize("doc_type", PORTED_TYPES)
    def test_lists_every_field_and_the_declared_type(self, doc_type):
        spec = get_doc_type_spec(doc_type)

        prompt = build_prompt(doc_type)

        assert f"('{doc_type}')" in prompt
        assert spec["document_label"] in prompt
        assert f"usually contains '{spec['expected_doc_type']}'" in prompt
        for name in spec["fields"]:
            assert f"- {name}: " in prompt

    @pytest.mark.parametrize("doc_type", PORTED_TYPES)
    def test_always_asks_for_the_common_keys(self, doc_type):
        prompt = build_prompt(doc_type)

        assert "detected_type" in prompt
        assert "issuing_state" in prompt
        assert "expiry_source" in prompt
        assert "'printed'" in prompt
        assert "'rule'" in prompt
        assert "'none'" in prompt
        assert "Never invent, compute or infer dates" in prompt
        assert "unknown" in prompt

    def test_expiry_field_hint(self):
        assert "read from the field 'expiry_year'" in build_prompt("ine")
        assert "read from the field 'coverage_end'" in build_prompt("insurance_policy")
        assert "usually has no printed expiry" in build_prompt("invoice")

    def test_type_hints_are_included(self):
        assert "factura sin valor" in build_prompt("invoice")

    def test_multi_file_note(self):
        assert "The 2 attached files are parts of the same document" in build_prompt("ine", file_count=2)
        assert "attached files" not in build_prompt("ine", file_count=1)

    def test_taxonomy_lists_every_type_and_unknown(self):
        prompt = build_prompt("invoice")

        for name in taxonomy():
            assert f"- {name}: " in prompt


class TestExtractionSpec:
    """Only analyzable types with fields can be extracted."""

    @pytest.mark.parametrize("doc_type", ["plates", "amortization_table", "driver_license", "unknown", "nope"])
    def test_rejects_types_without_definition(self, doc_type):
        with pytest.raises(ExtractionError, match="no extraction definition"):
            extraction_spec(doc_type)

    def test_taxonomy_ends_with_unknown(self):
        values = taxonomy()

        assert values[-1] == "unknown"
        assert values.count("unknown") == 1
        assert {"invoice_letter", "tax_status_certificate"}.issubset(values)
