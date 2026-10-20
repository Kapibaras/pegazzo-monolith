"""Tests for the BaseTask class."""

from __future__ import annotations

from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from app.worker.base import BaseTask


class ConcreteTask(BaseTask):
    """A concrete task for testing that overrides abstract methods."""

    name = "test.concrete_task"
    terminal_ids: ClassVar[set] = set()
    processing_ids: ClassVar[set] = set()
    failed_records: ClassVar[dict] = {}

    def process(self, record_id, *_args, **_kwargs):
        """Process a record."""
        return {"record_id": record_id, "status": "done"}

    def is_terminal(self, record_id):
        """Check terminal state."""
        return record_id in self.terminal_ids

    def mark_processing(self, record_id):
        """Mark as processing."""
        self.processing_ids.add(record_id)

    def mark_failed(self, record_id, reason):
        """Mark as failed."""
        self.failed_records[record_id] = reason

    def reset(self):
        """Reset test state."""
        self.terminal_ids = set()
        self.processing_ids = set()
        self.failed_records = {}


@pytest.fixture
def task():
    """Create a fresh ConcreteTask for testing."""
    t = ConcreteTask()
    t.reset()
    return t


class TestIdempotencyGuard:
    """The task should skip records already in terminal state."""

    def test_skips_terminal_record(self, task):
        """Record in terminal state is skipped."""
        task.terminal_ids.add(42)

        result = task.run_with_lifecycle(42)

        assert result["status"] == "skipped"
        assert result["reason"] == "already_terminal"
        assert 42 not in task.processing_ids

    def test_processes_non_terminal_record(self, task):
        """Non-terminal record is processed normally."""
        result = task.run_with_lifecycle(42)

        assert result["record_id"] == 42
        assert result["status"] == "done"
        assert 42 in task.processing_ids


class TestFailureHandling:
    """The task should mark records as failed on exceptions."""

    def test_marks_failed_on_exception(self, task):
        """Exception during process triggers failure handling."""

        def failing_process(_record_id, *_args, **_kwargs):
            raise RuntimeError("boom")

        task.process = failing_process

        with pytest.raises(RuntimeError, match="boom"):
            task.run_with_lifecycle(99)

    def test_marks_processing_before_execution(self, task):
        """Record is marked as processing before process() runs."""
        processed = []

        def tracking_process(record_id, *_args, **_kwargs):
            processed.append(record_id in task.processing_ids)
            return {"status": "done"}

        task.process = tracking_process
        task.run_with_lifecycle(10)

        assert processed == [True]


class TestSessionLifecycle:
    """The DB session should be created lazily and closed after return."""

    @patch("app.worker.base.SessionLocal")
    def test_session_created_on_access(self, mock_session_cls):
        """Session is created on first access to db property."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        task = BaseTask()
        _ = task.db

        mock_session_cls.assert_called_once()

    @patch("app.worker.base.SessionLocal")
    def test_session_closed_after_return(self, mock_session_cls):
        """Session is closed and cleared after task return."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        task = BaseTask()
        _ = task.db
        task.after_return("SUCCESS", None, "id", (), {}, None)

        mock_session.close.assert_called_once()

    def test_no_session_if_never_accessed(self):
        """No error if after_return is called without accessing db."""
        task = BaseTask()
        task.after_return("SUCCESS", None, "id", (), {}, None)
