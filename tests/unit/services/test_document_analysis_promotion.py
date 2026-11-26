import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.auth import AuthUser
from app.enum.auth import Role
from app.enum.crm import DocumentEntityType
from app.errors.database import DBOperationError
from app.errors.document_analysis import (
    AnalysisConsumedException,
    AnalysisDuplicatedException,
    AnalysisFileMissingException,
    AnalysisNotAnalyzedException,
    AnalysisNotFoundException,
    DocumentTypeNotAllowedException,
    ManualEntryNotAllowedException,
    ManualEntryRequiresOwnerException,
)
from app.models import Document, DocumentAnalysis, car_document_table, driver_document_table, guarantor_document_table
from app.repositories.document import DocumentRepository
from app.repositories.document_analysis import DocumentAnalysisRepository
from app.services.document_analysis import (
    DocumentAnalysisService,
    FinalValues,
    PromotionResult,
    finalize_promotion,
    rollback_promotion,
)
from app.storage.r2 import StoredObject
from app.storage.r2 import delete_documents_best_effort as real_delete_best_effort

OWNER = AuthUser(username="owner1", role=Role.OWNER)
ADMIN = AuthUser(username="admin1", role=Role.ADMIN)
CAR_ID = "CAR-0001"
DRIVER_ID = "CD-ABC-0001"
CAR_TYPES = {"circulation_card", "invoice", "plates"}
DRIVER_TYPES = {"ine", "driver_license", "proof_of_address"}
R2 = "app.services.document_analysis.r2"

pytestmark = pytest.mark.usefixtures("storage")


@pytest.fixture
def storage():
    """Mock R2: every temporary file exists, copies succeed."""
    with (
        patch(f"{R2}.head_document", return_value=StoredObject(size=10, content_type="image/jpeg")) as head,
        patch(f"{R2}.copy_document") as copy,
        patch(f"{R2}.delete_documents_best_effort") as delete,
    ):
        yield {"head": head, "copy": copy, "delete": delete}


@pytest.fixture
def service(analysis_db):
    return DocumentAnalysisService(DocumentAnalysisRepository(analysis_db), DocumentRepository(analysis_db))


def _analysis(db, declared_type="circulation_card", status="analyzed", files=1, created_by="owner1", **kwargs):
    analysis_id = uuid.uuid4()
    analysis = DocumentAnalysis(
        id=analysis_id,
        declared_type=declared_type,
        files=[{"key": f"tmp/analysis/{analysis_id}/{i}.jpg", "content_type": "image/jpeg", "size": 10} for i in range(files)],
        status=status,
        created_by=created_by,
        created_at=datetime.now(UTC),
        **kwargs,
    )
    db.add(analysis)
    db.commit()
    return analysis


def _promote(service, *, entity_type=DocumentEntityType.CAR, entity_id=CAR_ID, ids=(), manual=(), types=None, **kw):
    return service.promote_analyses(
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_ids=list(ids),
        manual_analysis_ids=list(manual),
        allowed_types=types if types is not None else CAR_TYPES | DRIVER_TYPES,
        final_values=kw.get("final_values", {}),
        caller=kw.get("caller", OWNER),
    )


def _documents(db):
    return db.query(Document).all()


class TestAnalyzedPromotion:
    """Analyzed documents become valid final documents."""

    def test_creates_document_and_consumes_analysis(self, analysis_db, service, storage):
        analysis = _analysis(
            analysis_db,
            extracted_fields={"plate": {"value": "ABC123", "check": "pass"}, "vin": "3VW..."},
            detected_type="circulation_card",
            model_version="gemini-3.6-flash",
            analyzed_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
        expiry = datetime(2027, 6, 30, tzinfo=UTC)
        final = {analysis.id: FinalValues(fields={"plate": "ABC-123", "owner": "Juan"}, expiry_date=expiry)}

        result = _promote(service, ids=[analysis.id], final_values=final)
        analysis_db.commit()

        documents = _documents(analysis_db)
        assert len(documents) == 1
        doc = documents[0]
        assert doc.analysis_id == analysis.id
        assert doc.type == "circulation_card"
        assert doc.category == "UNCLASSIFIED"
        assert doc.status == "valid"
        assert doc.verified_by == "owner1"
        assert doc.verified_at is not None
        assert doc.detected_type == "circulation_card"
        assert doc.model_version == "gemini-3.6-flash"
        assert doc.analyzed_at is not None
        assert doc.expiry_date.replace(tzinfo=UTC) == expiry
        assert doc.extracted_fields == {
            "plate": {"value": "ABC123", "check": "pass", "final": "ABC-123"},
            "vin": {"value": "3VW...", "check": None, "final": None},
            "owner": {"value": None, "check": None, "final": "Juan"},
        }
        assert doc.url.startswith(f"car/{CAR_ID}/")
        assert doc.url.endswith(".jpg")

        links = analysis_db.execute(select(car_document_table)).all()
        assert [(link.car_id, link.document_id) for link in links] == [(CAR_ID, doc.id)]

        analysis_db.refresh(analysis)
        assert analysis.status == "consumed"
        assert analysis.consumed_at is not None

        assert result.documents == [doc]
        assert result.temp_keys == [analysis.files[0]["key"]]
        assert result.final_keys == [doc.url]
        storage["copy"].assert_called_once_with(analysis.files[0]["key"], doc.url)
        storage["delete"].assert_not_called()

    def test_expiry_falls_back_to_prefill(self, analysis_db, service):
        analysis = _analysis(analysis_db, prefill={"expiry_date": "2028-01-15"})

        result = _promote(service, ids=[analysis.id])

        assert result.documents[0].expiry_date == datetime(2028, 1, 15, tzinfo=UTC)

    def test_saved_expiry_wins_over_prefill(self, analysis_db, service):
        analysis = _analysis(analysis_db, prefill={"expiry_date": "2028-01-15T00:00:00-06:00"})
        saved = datetime(2029, 1, 1, tzinfo=UTC)

        result = _promote(service, ids=[analysis.id], final_values={analysis.id: FinalValues(expiry_date=saved)})

        assert result.documents[0].expiry_date == saved

    def test_invalid_or_missing_prefill_expiry_is_none(self, analysis_db, service):
        bad = _analysis(analysis_db, prefill={"expiry_date": "not a date"})
        empty = _analysis(analysis_db, declared_type="invoice")

        result = _promote(service, ids=[bad.id, empty.id])

        assert [d.expiry_date for d in result.documents] == [None, None]

    def test_prefill_with_timezone_is_normalized_to_utc(self, analysis_db, service):
        analysis = _analysis(analysis_db, prefill={"expiry_date": "2028-01-15T00:00:00-06:00"})

        result = _promote(service, ids=[analysis.id])

        assert result.documents[0].expiry_date == datetime(2028, 1, 15, 6, tzinfo=UTC)

    def test_ine_two_files_creates_two_documents(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="ine", files=2, extracted_fields={"curp": "X"})

        result = _promote(service, entity_type=DocumentEntityType.DRIVER, entity_id=DRIVER_ID, ids=[analysis.id])
        analysis_db.commit()

        documents = _documents(analysis_db)
        assert len(documents) == 2
        assert {d.type for d in documents} == {"ine"}
        assert {d.analysis_id for d in documents} == {analysis.id}
        assert all(d.url.startswith(f"driver/{DRIVER_ID}/") for d in documents)
        assert len(result.temp_keys) == 2
        assert len(set(result.final_keys)) == 2
        links = analysis_db.execute(select(driver_document_table)).all()
        assert {link.document_id for link in links} == {d.id for d in documents}

    def test_links_guarantor_by_integer_id(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="ine")

        _promote(service, entity_type=DocumentEntityType.GUARANTOR, entity_id="7", ids=[analysis.id])

        links = analysis_db.execute(select(guarantor_document_table)).all()
        assert [link.guarantor_id for link in links] == [7]

    def test_links_garage(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="proof_of_address")

        result = _promote(service, entity_type=DocumentEntityType.GARAGE, entity_id="3", ids=[analysis.id])

        assert result.documents[0].url.startswith("garage/3/")


class TestEvidenceOnlyPromotion:
    """Evidence-only types (plates) are promoted from uploaded, without analysis."""

    def test_plates_from_uploaded(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="plates", status="uploaded")

        result = _promote(service, ids=[analysis.id])

        doc = result.documents[0]
        assert doc.status == "not_analyzed"
        assert doc.verified_by is None
        assert doc.verified_at is None
        assert doc.extracted_fields is None

    def test_plates_not_uploaded_is_rejected(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="plates", status="failed")

        with pytest.raises(AnalysisNotAnalyzedException):
            _promote(service, ids=[analysis.id])


class TestPromotionRejections:
    """Every analysis is validated before anything is copied or written."""

    def test_other_users_analysis_is_not_found(self, analysis_db, service):
        analysis = _analysis(analysis_db, created_by="someone_else")

        with pytest.raises(AnalysisNotFoundException) as exc:
            _promote(service, ids=[analysis.id])

        assert exc.value.status_code == 404
        assert exc.value.code == "analysis_not_found"

    def test_unknown_analysis_is_not_found(self, service):
        with pytest.raises(AnalysisNotFoundException):
            _promote(service, ids=[uuid.uuid4()])

    def test_consumed_analysis(self, analysis_db, service):
        analysis = _analysis(analysis_db, status="consumed")

        with pytest.raises(AnalysisConsumedException) as exc:
            _promote(service, ids=[analysis.id])

        assert exc.value.status_code == 409
        assert exc.value.code == "analysis_consumed"

    @pytest.mark.parametrize("status", ["uploaded", "failed", "rejected"])
    def test_analyzable_without_analysis(self, analysis_db, service, status):
        analysis = _analysis(analysis_db, status=status)

        with pytest.raises(AnalysisNotAnalyzedException) as exc:
            _promote(service, ids=[analysis.id])

        assert exc.value.code == "analysis_not_analyzed"

    def test_type_not_allowed_for_section(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="invoice")

        with pytest.raises(DocumentTypeNotAllowedException) as exc:
            _promote(service, ids=[analysis.id], types={"circulation_card"})

        assert exc.value.code == "document_type_not_allowed"

    def test_type_not_allowed_for_entity(self, analysis_db, service):
        analysis = _analysis(analysis_db, declared_type="ine")

        with pytest.raises(DocumentTypeNotAllowedException):
            _promote(service, entity_type=DocumentEntityType.CAR, ids=[analysis.id], types={"ine"})

    def test_missing_temp_file(self, analysis_db, service, storage):
        analysis = _analysis(analysis_db, declared_type="ine", files=2)
        storage["head"].side_effect = [StoredObject(size=10, content_type="image/jpeg"), None]

        with pytest.raises(AnalysisFileMissingException) as exc:
            _promote(service, entity_type=DocumentEntityType.DRIVER, entity_id=DRIVER_ID, ids=[analysis.id])

        assert exc.value.code == "analysis_file_missing"
        storage["copy"].assert_not_called()
        assert _documents(analysis_db) == []

    def test_duplicated_analysis(self, analysis_db, service):
        analysis = _analysis(analysis_db)

        with pytest.raises(AnalysisDuplicatedException):
            _promote(service, ids=[analysis.id, analysis.id])

    def test_rejection_of_one_analysis_promotes_none(self, analysis_db, service, storage):
        good = _analysis(analysis_db)
        bad = _analysis(analysis_db, declared_type="invoice", status="uploaded")

        with pytest.raises(AnalysisNotAnalyzedException):
            _promote(service, ids=[good.id, bad.id])

        storage["copy"].assert_not_called()
        analysis_db.rollback()
        assert _documents(analysis_db) == []
        assert analysis_db.get(DocumentAnalysis, good.id).status == "analyzed"


class TestManualEntry:
    """Owners can save failed or rejected analyses as evidence with typed data."""

    def test_owner_after_provider_failure(self, analysis_db, service):
        analysis = _analysis(analysis_db, status="failed", reason="provider_unavailable")
        expiry = datetime(2027, 1, 1, tzinfo=UTC)

        result = _promote(service, manual=[analysis.id], final_values={analysis.id: FinalValues(expiry_date=expiry)})

        doc = result.documents[0]
        assert doc.status == "not_analyzed"
        assert doc.extracted_fields is None
        assert doc.verified_by == "owner1"
        assert doc.verified_at is not None
        assert doc.expiry_date == expiry
        assert analysis.status == "consumed"

    def test_owner_after_rejection(self, analysis_db, service):
        analysis = _analysis(analysis_db, status="rejected", reason="unreadable", prefill={"expiry_date": "2030-01-01"})

        result = _promote(service, manual=[analysis.id])

        doc = result.documents[0]
        assert doc.status == "not_analyzed"
        assert doc.expiry_date is None

    def test_manual_and_analyzed_together(self, analysis_db, service):
        analyzed = _analysis(analysis_db)
        failed = _analysis(analysis_db, declared_type="invoice", status="failed")

        result = _promote(service, ids=[analyzed.id], manual=[failed.id])

        assert [d.status for d in result.documents] == ["valid", "not_analyzed"]

    def test_admin_is_forbidden(self, analysis_db, service):
        analysis = _analysis(analysis_db, status="failed", created_by="admin1")

        with pytest.raises(ManualEntryRequiresOwnerException) as exc:
            _promote(service, manual=[analysis.id], caller=ADMIN)

        assert exc.value.status_code == 403
        assert exc.value.code == "manual_entry_requires_owner"

    def test_admin_can_promote_analyzed(self, analysis_db, service):
        analysis = _analysis(analysis_db, created_by="admin1")

        result = _promote(service, ids=[analysis.id], caller=ADMIN)

        assert result.documents[0].verified_by == "admin1"

    def test_wrong_document_is_not_allowed(self, analysis_db, service):
        analysis = _analysis(analysis_db, status="rejected", reason="wrong_document")

        with pytest.raises(ManualEntryNotAllowedException) as exc:
            _promote(service, manual=[analysis.id])

        assert exc.value.code == "manual_entry_not_allowed"

    @pytest.mark.parametrize("status", ["uploaded", "analyzed"])
    def test_only_failed_or_rejected(self, analysis_db, service, status):
        analysis = _analysis(analysis_db, status=status)

        with pytest.raises(ManualEntryNotAllowedException):
            _promote(service, manual=[analysis.id])


class TestPromotionRollback:
    """If anything fails nothing is created, copied finals are removed and temporary files stay."""

    def test_copy_failure_removes_copied_finals(self, analysis_db, service, storage):
        analysis = _analysis(analysis_db, declared_type="ine", files=2)
        storage["copy"].side_effect = [None, RuntimeError("R2 down")]

        with pytest.raises(RuntimeError):
            _promote(service, entity_type=DocumentEntityType.DRIVER, entity_id=DRIVER_ID, ids=[analysis.id])

        copied = storage["copy"].call_args_list[0].args[1]
        storage["delete"].assert_called_once_with([copied])
        analysis_db.rollback()
        assert _documents(analysis_db) == []
        assert analysis_db.get(DocumentAnalysis, analysis.id).status == "analyzed"

    def test_db_failure_after_copy_leaves_no_rows(self, analysis_db, service, storage):
        analysis = _analysis(analysis_db)

        with (
            patch.object(service.document_repository, "link_to_car", side_effect=DBOperationError("boom")),
            pytest.raises(DBOperationError),
        ):
            _promote(service, ids=[analysis.id])

        final_key = storage["copy"].call_args.args[1]
        storage["delete"].assert_called_once_with([final_key])
        analysis_db.rollback()
        assert _documents(analysis_db) == []
        assert analysis_db.get(DocumentAnalysis, analysis.id).status == "analyzed"

    def test_caller_failure_after_promotion_rolls_back(self, analysis_db, service, storage):
        analysis = _analysis(analysis_db)

        result = _promote(service, ids=[analysis.id])
        # The section endpoint fails before committing (e.g. saving the car): it rolls back and cleans up.
        analysis_db.rollback()
        rollback_promotion(result)

        assert _documents(analysis_db) == []
        assert analysis_db.get(DocumentAnalysis, analysis.id).status == "analyzed"
        storage["delete"].assert_called_once_with(result.final_keys)

    def test_promotion_never_commits(self, analysis_db, service):
        analysis = _analysis(analysis_db)

        with patch.object(analysis_db, "commit", side_effect=AssertionError("promotion must not commit")):
            _promote(service, ids=[analysis.id])


class TestFinalizeAndRollbackHelpers:
    """Best-effort storage cleanup after commit / rollback."""

    def test_finalize_deletes_temp_keys(self):
        result = PromotionResult(temp_keys=["tmp/a/0.jpg"], final_keys=["car/X/1.jpg"])

        with patch(f"{R2}.delete_documents_best_effort") as delete:
            finalize_promotion(result)

        delete.assert_called_once_with(["tmp/a/0.jpg"])

    def test_finalize_is_best_effort(self):
        result = PromotionResult(temp_keys=["tmp/a/0.jpg", "tmp/a/1.jpg"])

        with (
            patch(f"{R2}.delete_documents_best_effort", real_delete_best_effort),
            patch("app.storage.r2.delete_document", side_effect=RuntimeError("R2 down")) as delete,
        ):
            finalize_promotion(result)

        assert delete.call_count == 2

    def test_rollback_deletes_final_keys(self):
        result = PromotionResult(temp_keys=["tmp/a/0.jpg"], final_keys=["car/X/1.jpg"])

        with patch(f"{R2}.delete_documents_best_effort") as delete:
            rollback_promotion(result)

        delete.assert_called_once_with(["car/X/1.jpg"])
