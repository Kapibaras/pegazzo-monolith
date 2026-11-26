"""Hourly cleanup of temporary document analyses that were never consumed (PGZ-179).

Deletes ``document_analysis`` rows not consumed after ``DocumentConfig.ANALYSIS_RETENTION_HOURS`` (24 h) and then
their temporary files, best effort. The R2 lifecycle rule on ``private/tmp/`` (1 day) is the safety net for files
this task could not delete. Logs counts only.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from app.config.constants import DocumentConfig
from app.repositories.document_analysis import DocumentAnalysisRepository
from app.storage import r2
from app.worker.base import BaseTask
from app.worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="app.worker.tasks.analysis_cleanup.cleanup_expired_analyses", base=BaseTask, bind=True)
def cleanup_expired_analyses(self: BaseTask) -> dict:
    """Delete expired, not consumed analyses and their temporary files."""
    cutoff = datetime.now(UTC) - timedelta(hours=DocumentConfig.ANALYSIS_RETENTION_HOURS)
    repository = DocumentAnalysisRepository(self.db)

    expired = repository.list_expired(cutoff)
    keys = [file["key"] for analysis in expired for file in analysis.files or []]
    deleted = repository.delete_many([analysis.id for analysis in expired])
    # Rows first: if the DB delete fails nothing is lost and the next run retries. Files after the commit, best effort.
    r2.delete_documents_best_effort(keys)

    logger.info("Analysis cleanup: %d expired analyses deleted, %d temporary files removed", deleted, len(keys))
    return {"deleted": deleted, "files": len(keys)}
