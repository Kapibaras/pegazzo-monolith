from __future__ import annotations

import logging
import time

from celery import Task

from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base task that manages its own database session lifecycle.

    Concrete tasks inherit from this and get a fresh SQLAlchemy session
    independent of the FastAPI request scope. The session is automatically
    closed in ``after_return``.
    """

    abstract = True
    _db = None

    @property
    def db(self):
        """Return a lazy-initialized SQLAlchemy session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *_args, **_kwargs):
        """Close the database session after the task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def run_with_lifecycle(self, record_id: int, *args, **kwargs):
        """Execute the task with idempotency guard and consistent failure handling.

        Subclasses implement ``process(record_id, ...)`` instead of ``run``.
        """
        start = time.monotonic()
        try:
            task_id = self.request.id or "eager"
        except (AttributeError, TypeError):
            task_id = "eager"

        if self.is_terminal(record_id):
            logger.info(
                "Task %s skipped: record %s already in terminal state",
                task_id,
                record_id,
            )
            return {"status": "skipped", "reason": "already_terminal"}

        self.mark_processing(record_id)
        try:
            result = self.process(record_id, *args, **kwargs)
        except Exception:
            duration = time.monotonic() - start
            logger.exception(
                "Task %s failed for record %s after %.2fs",
                task_id,
                record_id,
                duration,
            )
            self._safe_mark_failed(record_id, reason="task_error")
            raise
        else:
            duration = time.monotonic() - start
            logger.info(
                "Task %s completed for record %s in %.2fs",
                task_id,
                record_id,
                duration,
            )
            return result

    def process(self, record_id: int, *args, **kwargs):
        """Override in concrete tasks with the actual work."""
        raise NotImplementedError

    def is_terminal(self, record_id: int) -> bool:
        """Check if ``record_id`` is already in a terminal state.

        Override in concrete tasks. Returns False by default (no guard).
        TODO PGZ-124: implement using AnalysisRequest status check.
        Terminal states: valid, review, rejected, failed.
        """
        del record_id  # used by concrete implementations
        return False

    def mark_processing(self, record_id: int) -> None:
        """Mark the record as processing.

        Override in concrete tasks to set the status on the record.
        TODO PGZ-124: set AnalysisRequest.status = 'processing'.
        """

    def mark_failed(self, record_id: int, reason: str) -> None:
        """Mark the record as failed with a reason.

        Override in concrete tasks to persist the failure.
        TODO PGZ-124: set AnalysisRequest.status = 'failed', failure_reason = reason.
        """

    def _safe_mark_failed(self, record_id: int, reason: str) -> None:
        """Mark failed with its own commit.

        The state persists even if the main transaction rolled back.
        """
        try:
            session = SessionLocal()
            try:
                self.mark_failed(record_id, reason)
                session.commit()
            finally:
                session.close()
        except Exception:
            logger.exception(
                "Failed to mark record %s as failed (reason: %s)",
                record_id,
                reason,
            )
