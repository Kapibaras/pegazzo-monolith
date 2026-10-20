"""Tests for the retry policy helper."""

from unittest.mock import patch

import pytest

from app.worker.retry import (
    BUDGET_SECONDS,
    BudgetExhaustedError,
    ProviderUnavailableError,
    with_retries,
)


class TestRetryBackoffSequence:
    """Verify the backoff waits match the expected sequence."""

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_backoff_sequence(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 0, 5, 5, 20, 20, 65, 65]
        call_count = 0

        def failing_fn():
            nonlocal call_count
            call_count += 1
            raise ProviderUnavailableError("unavailable", status_code=503)

        with pytest.raises(BudgetExhaustedError) as exc_info:
            with_retries(failing_fn)

        assert exc_info.value.attempts == 4
        waits = [call.args[0] for call in mock_sleep.call_args_list]
        assert waits == [5, 15, 45, 90]

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_succeeds_on_second_attempt(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 0, 5]
        calls = []

        def flaky_fn():
            calls.append(1)
            if len(calls) == 1:
                raise ProviderUnavailableError("temporary", status_code=503)
            return "ok"

        result = with_retries(flaky_fn)

        assert result == "ok"
        assert len(calls) == 2
        assert mock_sleep.call_count == 1


class TestRetryAfterHeader:
    """Verify the Retry-After header is honored."""

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_honors_retry_after(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 0, 30, 30]
        calls = []

        def fn_with_retry_after():
            calls.append(1)
            if len(calls) == 1:
                raise ProviderUnavailableError("rate limited", status_code=429, retry_after=30)
            return "ok"

        result = with_retries(fn_with_retry_after)

        assert result == "ok"
        assert mock_sleep.call_args_list[0].args[0] == 30

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_retry_after_capped_by_remaining_budget(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0, 0, 170]
        calls = []

        def fn_with_long_retry_after():
            calls.append(1)
            if len(calls) == 1:
                raise ProviderUnavailableError("rate limited", status_code=429, retry_after=60)
            return "ok"

        with_retries(fn_with_long_retry_after)

        wait_used = mock_sleep.call_args_list[0].args[0]
        assert wait_used <= BUDGET_SECONDS


class TestBudgetExhaustion:
    """Verify the retry budget is enforced."""

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_budget_exhausted_raises(self, mock_monotonic, _mock_sleep):
        mock_monotonic.side_effect = [0, 0, 50, 50, 120, 120, 170, 170, 200]

        def always_failing():
            raise ProviderUnavailableError("down", status_code=503)

        with pytest.raises(BudgetExhaustedError) as exc_info:
            with_retries(always_failing)

        assert exc_info.value.attempts == 4

    @patch("app.worker.retry.time.sleep")
    @patch("app.worker.retry.time.monotonic")
    def test_stops_early_when_budget_spent_mid_sequence(self, mock_monotonic, mock_sleep):
        # start=0, elapsed check after 1st fail=BUDGET+1 → break, final elapsed=BUDGET+1
        mock_monotonic.side_effect = [0, BUDGET_SECONDS + 1, BUDGET_SECONDS + 1]

        def always_failing():
            raise ProviderUnavailableError("down", status_code=503)

        with pytest.raises(BudgetExhaustedError):
            with_retries(always_failing)

        assert mock_sleep.call_count == 0


class TestNonRetryableErrors:
    """Errors that are not ProviderUnavailableError propagate immediately."""

    def test_non_provider_error_propagates(self):
        def bad_fn():
            raise ValueError("not a provider error")

        with pytest.raises(ValueError, match="not a provider error"):
            with_retries(bad_fn)
