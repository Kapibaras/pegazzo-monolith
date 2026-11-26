"""Tests for the hourly cleanup of expired document analyses."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.models import DocumentAnalysis
from app.worker.tasks.analysis_cleanup import cleanup_expired_analyses

STORAGE = "app.worker.tasks.analysis_cleanup.r2.delete_documents_best_effort"


def _add(db, *, status="uploaded", hours_old=0, files=1):
    analysis_id = uuid.uuid4()
    db.add(
        DocumentAnalysis(
            id=analysis_id,
            declared_type="ine",
            files=[
                {"key": f"tmp/analysis/{analysis_id}/{i}.jpg", "content_type": "image/jpeg", "size": 1} for i in range(files)
            ],
            status=status,
            created_by="owner1",
            created_at=datetime.now(UTC) - timedelta(hours=hours_old),
        ),
    )
    db.commit()
    return analysis_id


@pytest.fixture
def task_db(analysis_db):
    """Make the task's BaseTask session the SQLite test session."""
    with patch("app.worker.base.SessionLocal", return_value=analysis_db):
        yield analysis_db
    cleanup_expired_analyses.after_return()


class TestAnalysisCleanup:
    """cleanup_expired_analyses removes only old, not consumed analyses."""

    def test_deletes_old_not_consumed_rows_and_their_files(self, task_db):
        expired_uploaded = _add(task_db, hours_old=25, files=2)
        expired_failed = _add(task_db, status="failed", hours_old=30)
        consumed = _add(task_db, status="consumed", hours_old=48)
        recent = _add(task_db, hours_old=1)

        with patch(STORAGE) as delete:
            result = cleanup_expired_analyses()

        assert result == {"deleted": 2, "files": 3}
        remaining = {a.id for a in task_db.query(DocumentAnalysis).all()}
        assert remaining == {consumed, recent}
        deleted_keys = delete.call_args.args[0]
        assert sorted(deleted_keys) == sorted(
            [
                f"tmp/analysis/{expired_uploaded}/0.jpg",
                f"tmp/analysis/{expired_uploaded}/1.jpg",
                f"tmp/analysis/{expired_failed}/0.jpg",
            ],
        )

    def test_nothing_to_clean(self, task_db):
        _add(task_db, hours_old=2)

        with patch(STORAGE) as delete:
            result = cleanup_expired_analyses()

        assert result == {"deleted": 0, "files": 0}
        delete.assert_called_once_with([])

    def test_tolerates_storage_errors(self, task_db):
        _add(task_db, hours_old=25)

        with patch("app.storage.r2.delete_document", side_effect=RuntimeError("R2 down")):
            result = cleanup_expired_analyses()

        assert result == {"deleted": 1, "files": 1}
        assert task_db.query(DocumentAnalysis).count() == 0

    def test_scheduled_hourly_on_documents_queue(self):
        import app.worker.beat_schedules  # registers the beat schedule
        from app.worker.celery_app import app

        entry = app.conf.beat_schedule["cleanup-expired-analyses"]
        assert entry["task"] == "app.worker.tasks.analysis_cleanup.cleanup_expired_analyses"
        assert entry["options"] == {"queue": "documents"}
        assert entry["schedule"].minute == {0}
        assert entry["schedule"].hour == set(range(24))
        assert "check-stuck-tasks" in app.conf.beat_schedule
