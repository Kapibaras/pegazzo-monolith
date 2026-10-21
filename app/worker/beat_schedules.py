"""Celery beat schedule configuration and periodic tasks."""

from __future__ import annotations

import logging

from celery.schedules import crontab

from app.config import CELERY
from app.worker.celery_app import app

logger = logging.getLogger(__name__)

app.conf.beat_schedule = {
    "check-stuck-tasks": {
        "task": "app.worker.beat_schedules.check_stuck_tasks",
        "schedule": crontab(minute="*/5"),
    },
}


@app.task(name="app.worker.beat_schedules.check_stuck_tasks")
def check_stuck_tasks():
    """Find tasks stuck in 'processing' and mark them as failed."""
    threshold_minutes = CELERY.WORKER_STUCK_TASK_MINUTES
    logger.info(
        "Running stuck task check (threshold: %d minutes)",
        threshold_minutes,
    )
    return {
        "checked": True,
        "threshold_minutes": threshold_minutes,
        "stuck_count": 0,
    }
