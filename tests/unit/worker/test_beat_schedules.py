"""Tests for the stuck task check beat schedule."""

from unittest.mock import patch


class TestStuckTaskCheck:
    """Verify the stuck task check periodic task."""

    @patch("app.worker.beat_schedules.CELERY")
    def test_check_stuck_tasks_returns_result(self, mock_celery):
        mock_celery.WORKER_STUCK_TASK_MINUTES = 10

        from app.worker.beat_schedules import check_stuck_tasks

        result = check_stuck_tasks()

        assert result["checked"] is True
        assert result["threshold_minutes"] == 10
        assert result["stuck_count"] == 0

    def test_beat_schedule_is_configured(self):
        from app.worker.celery_app import app

        assert "check-stuck-tasks" in app.conf.beat_schedule
        schedule_entry = app.conf.beat_schedule["check-stuck-tasks"]
        assert schedule_entry["task"] == "app.worker.beat_schedules.check_stuck_tasks"
