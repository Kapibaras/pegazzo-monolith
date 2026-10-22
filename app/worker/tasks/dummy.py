"""Dummy task for verifying the Celery infrastructure end-to-end.

This task exists solely for testing that the broker, worker and beat
are wired correctly. Remove once real tasks (PGZ-124) are in place.
"""

from __future__ import annotations

import logging

from app.worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="app.worker.tasks.dummy.ping")
def ping(message: str = "pong"):
    """Echo task — returns the message it receives."""
    logger.info("Ping task executed with message: %s", message)
    return {"message": message}
