import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.errors.database import DBOperationError
from app.models import Document, DocumentAnalysis
from app.repositories.document import DocumentRepository
from app.repositories.document_analysis import DocumentAnalysisRepository


def _new(status="uploaded", created_at=None):
    return DocumentAnalysis(
        id=uuid.uuid4(),
        declared_type="ine",
        files=[{"key": "tmp/analysis/x/0.jpg", "content_type": "image/jpeg", "size": 1}],
        status=status,
        created_by="owner1",
        created_at=created_at or datetime.now(UTC),
    )


class TestDocumentAnalysisRepository:
    """DocumentAnalysisRepository against a real SQLite session."""

    def test_create_and_get_many(self, analysis_db):
        repo = DocumentAnalysisRepository(analysis_db)
        first, second = repo.create(_new()), repo.create(_new())

        found = repo.get_many_for_update([first.id, second.id, uuid.uuid4()])

        assert set(found) == {first.id, second.id}

    def test_get_many_with_no_ids(self, analysis_db):
        assert DocumentAnalysisRepository(analysis_db).get_many_for_update([]) == {}

    def test_mark_consumed_only_flushes(self, analysis_db):
        repo = DocumentAnalysisRepository(analysis_db)
        analysis = repo.create(_new(status="analyzed"))
        now = datetime.now(UTC)

        repo.mark_consumed(analysis, now)
        analysis_db.rollback()

        assert analysis_db.get(DocumentAnalysis, analysis.id).status == "analyzed"

    def test_list_expired_and_delete_many(self, analysis_db):
        repo = DocumentAnalysisRepository(analysis_db)
        old = datetime.now(UTC) - timedelta(hours=25)
        expired = repo.create(_new(created_at=old))
        consumed = repo.create(_new(status="consumed", created_at=old))
        recent = repo.create(_new())

        cutoff = datetime.now(UTC) - timedelta(hours=24)
        assert [a.id for a in repo.list_expired(cutoff)] == [expired.id]

        assert repo.delete_many([expired.id, consumed.id]) == 1
        remaining = {a.id for a in analysis_db.query(DocumentAnalysis).all()}
        assert remaining == {consumed.id, recent.id}

    def test_delete_many_with_no_ids(self, analysis_db):
        assert DocumentAnalysisRepository(analysis_db).delete_many([]) == 0

    def test_create_failure_rolls_back(self):
        db = Mock(spec=Session)
        db.commit.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError):
            DocumentAnalysisRepository(db).create(_new())

        db.rollback.assert_called_once()

    def test_mark_consumed_failure(self):
        db = Mock(spec=Session)
        db.flush.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError):
            DocumentAnalysisRepository(db).mark_consumed(_new(), datetime.now(UTC))

        db.rollback.assert_not_called()

    def test_delete_many_failure_rolls_back(self):
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.delete.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError):
            DocumentAnalysisRepository(db).delete_many([uuid.uuid4()])

        db.rollback.assert_called_once()

    def test_commit_and_rollback_passthrough(self):
        db = Mock(spec=Session)
        repo = DocumentAnalysisRepository(db)

        repo.commit()
        repo.rollback()

        db.commit.assert_called_once()
        db.rollback.assert_called_once()


class TestDocumentRepositoryCommitFlag:
    """``commit=False`` joins the caller's transaction; the default keeps committing."""

    def test_create_without_commit_only_flushes(self, analysis_db):
        repo = DocumentRepository(analysis_db)
        document = repo.create(Document(type="ine", url="driver/X/1.jpg"), commit=False)

        assert document.id is not None
        analysis_db.rollback()
        assert analysis_db.query(Document).count() == 0

    def test_create_with_commit_persists(self, analysis_db):
        DocumentRepository(analysis_db).create(Document(type="ine", url="driver/X/1.jpg"))
        analysis_db.rollback()

        assert analysis_db.query(Document).count() == 1

    def test_create_without_commit_failure_does_not_roll_back(self):
        db = Mock(spec=Session)
        db.flush.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError):
            DocumentRepository(db).create(Document(type="ine", url="x"), commit=False)

        db.rollback.assert_not_called()

    def test_create_with_commit_failure_rolls_back(self):
        db = Mock(spec=Session)
        db.commit.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError):
            DocumentRepository(db).create(Document(type="ine", url="x"))

        db.rollback.assert_called_once()

    @pytest.mark.parametrize(
        ("method", "entity_id"),
        [("link_to_car", "CAR1"), ("link_to_driver", "DRV1"), ("link_to_guarantor", 1), ("link_to_garage", 1)],
    )
    def test_link_commit_flag(self, method, entity_id):
        db = Mock(spec=Session)
        repo = DocumentRepository(db)

        getattr(repo, method)(1, entity_id, commit=False)
        db.commit.assert_not_called()

        getattr(repo, method)(1, entity_id)
        db.commit.assert_called_once()

    @pytest.mark.parametrize("commit", [True, False])
    def test_link_failure(self, commit):
        db = Mock(spec=Session)
        db.execute.side_effect = RuntimeError("db down")

        with pytest.raises(DBOperationError, match="Error linking document to car"):
            DocumentRepository(db).link_to_car(1, "CAR1", commit=commit)

        assert db.rollback.called is commit
