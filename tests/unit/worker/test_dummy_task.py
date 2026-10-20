"""Tests for the dummy ping task."""


class TestDummyTask:
    """Verify the dummy task works in eager mode."""

    def test_ping_returns_message(self):
        from app.worker.tasks.dummy import ping

        result = ping("hello")

        assert result == {"message": "hello"}

    def test_ping_default_message(self):
        from app.worker.tasks.dummy import ping

        result = ping()

        assert result == {"message": "pong"}
