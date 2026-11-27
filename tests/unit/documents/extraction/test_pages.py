from io import BytesIO
from unittest.mock import patch

import pytest
from pypdf import PdfReader

from app.config.constants import ExtractionConfig
from app.documents.extraction.base import ExtractionFile
from app.documents.extraction.errors import ExtractionError, InputTooLargeError
from app.documents.extraction.pages import page_strategy, prepare_file, prepare_files, select_pages
from app.documents.registry import get_all_specs


class TestPageStrategyPerType:
    """Configured pages per type (PGZ-164 page strategy table)."""

    @pytest.mark.parametrize(
        ("doc_type", "total", "expected"),
        [
            ("amortization_table", 6, [0]),
            ("credit_contract", 8, [0, 1, 7]),
            ("insurance_policy", 7, [0, 1]),
            ("ine", 2, [0, 1]),
            ("circulation_card", 3, [0, 1, 2]),
            ("invoice", 5, [0, 1, 2]),
            ("invoice_letter", 5, [0, 1, 2]),
            ("tax_status_certificate", 4, [0, 1, 2]),
        ],
    )
    def test_pages_kept(self, doc_type, total, expected):
        assert select_pages(total, page_strategy(doc_type)) == expected

    @pytest.mark.parametrize(
        ("total", "expected"),
        [(1, [0]), (2, [0, 1]), (3, [0, 1, 2])],
    )
    def test_first_two_plus_last_on_short_documents(self, total, expected):
        assert select_pages(total, {"first": 2, "last": 1}) == expected

    def test_unknown_type_uses_default(self):
        assert page_strategy("not_a_type") == ExtractionConfig.DEFAULT_PAGES

    @pytest.mark.parametrize("strategy", ["some", {"middle": 1}, {"first": 0}, {"first": -1}, None])
    def test_invalid_strategy(self, strategy):
        with pytest.raises(ValueError, match="Invalid page strategy"):
            select_pages(3, strategy)

    def test_every_registry_strategy_is_valid(self):
        for name in get_all_specs():
            assert select_pages(4, page_strategy(name)), name


class TestPrepareFile:
    """Images pass unchanged; PDFs are split with pypdf when the strategy drops pages."""

    def test_image_is_sent_unchanged(self, jpeg):
        prepared = prepare_file(ExtractionFile(jpeg, "image/jpeg"), {"first": 1})

        assert prepared.data == jpeg
        assert prepared.pages is None
        assert prepared.pages_sent == 1

    def test_pdf_is_split(self, pdf_factory):
        prepared = prepare_file(ExtractionFile(pdf_factory(8), "application/pdf"), {"first": 2, "last": 1})

        assert prepared.pages == [0, 1, 7]
        assert prepared.pages_sent == 3
        assert len(PdfReader(BytesIO(prepared.data)).pages) == 3

    def test_pdf_with_every_page_kept_is_sent_unchanged(self, pdf_factory):
        data = pdf_factory(2)

        prepared = prepare_file(ExtractionFile(data, "application/pdf"), "all")

        assert prepared.data == data
        assert prepared.pages is None
        assert prepared.pages_sent == 2

    def test_unreadable_pdf(self):
        with pytest.raises(ExtractionError, match="cannot be read"):
            prepare_file(ExtractionFile(b"not a pdf", "application/pdf"), "all")

    def test_unsupported_content_type(self, jpeg):
        with pytest.raises(ExtractionError, match="Unsupported content type"):
            prepare_file(ExtractionFile(jpeg, "image/gif"), "all")


class TestPrepareFiles:
    """The files of one analysis share the inline request limit."""

    def test_uses_the_type_strategy(self, pdf_factory):
        prepared = prepare_files([ExtractionFile(pdf_factory(5), "application/pdf")], "insurance_policy")

        assert prepared[0].pages == [0, 1]

    def test_two_ine_parts(self, jpeg):
        prepared = prepare_files([ExtractionFile(jpeg, "image/jpeg"), ExtractionFile(jpeg, "image/png")], "ine")

        assert [p.mime_type for p in prepared] == ["image/jpeg", "image/png"]

    def test_over_the_inline_limit(self, jpeg):
        with (
            patch.object(ExtractionConfig, "INLINE_REQUEST_MAX_BYTES", len(jpeg) * 2 - 1),
            pytest.raises(InputTooLargeError, match="inline limit"),
        ):
            prepare_files([ExtractionFile(jpeg, "image/jpeg"), ExtractionFile(jpeg, "image/jpeg")], "ine")
