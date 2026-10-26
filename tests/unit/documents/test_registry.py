from app.documents.registry import get_all_specs, get_analyzable_types, get_doc_type_spec, is_valid_for_entity
from app.enum.document import DocumentType


class TestDocumentRegistry:
    """Tests for the document type taxonomy registry."""

    def test_all_json_files_loaded(self):
        specs = get_all_specs()
        # Every DocumentType except 'unknown' must have a JSON file
        expected = {t.value for t in DocumentType if t != DocumentType.UNKNOWN}
        assert set(specs.keys()) == expected

    def test_every_spec_has_required_keys(self):
        for name, spec in get_all_specs().items():
            assert spec["name"] == name
            assert "label_es" in spec, f"{name} missing label_es"
            assert "allowed_entity_types" in spec, f"{name} missing allowed_entity_types"
            assert isinstance(spec["allowed_entity_types"], list)
            assert "has_expiry" in spec, f"{name} missing has_expiry"
            assert "ai_analyzable" in spec, f"{name} missing ai_analyzable"

    def test_get_doc_type_spec_known(self):
        spec = get_doc_type_spec("ine")
        assert spec is not None
        assert spec["name"] == "ine"
        assert spec["label_es"] == "INE / IFE (credencial para votar)"

    def test_get_doc_type_spec_unknown_returns_none(self):
        assert get_doc_type_spec("nonexistent") is None
        assert get_doc_type_spec("unknown") is None

    def test_is_valid_for_entity_car_types(self):
        assert is_valid_for_entity("circulation_card", "car") is True
        assert is_valid_for_entity("insurance_policy", "car") is True
        assert is_valid_for_entity("invoice", "car") is True
        assert is_valid_for_entity("contract", "car") is True

    def test_is_valid_for_entity_person_types(self):
        assert is_valid_for_entity("ine", "driver") is True
        assert is_valid_for_entity("ine", "guarantor") is True
        assert is_valid_for_entity("driver_license", "driver") is True

    def test_is_valid_for_entity_rejects_incompatible(self):
        assert is_valid_for_entity("ine", "car") is False
        assert is_valid_for_entity("circulation_card", "driver") is False
        assert is_valid_for_entity("driver_license", "car") is False

    def test_is_valid_for_entity_unknown_type(self):
        assert is_valid_for_entity("nonexistent", "car") is False

    def test_get_analyzable_types(self):
        analyzable = get_analyzable_types()
        assert "ine" in analyzable
        assert "circulation_card" in analyzable
        # These are not AI-analyzable
        assert "contract" not in analyzable
        assert "promissory_note" not in analyzable
        assert "plates" not in analyzable

    def test_has_expiry_flag(self):
        assert get_doc_type_spec("circulation_card")["has_expiry"] is True
        assert get_doc_type_spec("insurance_policy")["has_expiry"] is True
        assert get_doc_type_spec("ine")["has_expiry"] is True
        assert get_doc_type_spec("invoice")["has_expiry"] is False
        assert get_doc_type_spec("plates")["has_expiry"] is False
