"""Reusable retry policy for provider errors (503, 429, timeouts).

Backoff sequence: ~5s, ~15s, ~45s, ~90s (honoring Retry-After when present).
Total budget: ~3 minutes. After the budget is spent, the exception propagates
so the caller (BaseTask) can mark the record as failed.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {503, 429}
DEFAULT_BACKOFFS = [5, 15, 45, 90]
BUDGET_SECONDS = 180


class ProviderUnavailableError(Exception):
    """Raised when an AI provider returns a retryable error."""

    def __init__(self, message: str, status_code: int | None = None, retry_after: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class BudgetExhaustedError(Exception):
    """Raised when the retry budget has been fully spent."""

    def __init__(self, attempts: int, elapsed: float):
        self.attempts = attempts
        self.elapsed = elapsed
        super().__init__(
            f"Retry budget exhausted after {attempts} attempts ({elapsed:.1f}s)",
        )


def with_retries(fn, *args, **kwargs):
    """Call ``fn`` with automatic retries on ``ProviderUnavailableError``.

    Returns the result of ``fn`` on success. Raises ``BudgetExhaustedError``
    when the total retry budget is spent.
    """
    start = time.monotonic()
    last_error = None

    for attempt, default_wait in enumerate(DEFAULT_BACKOFFS, start=1):
        try:
            return fn(*args, **kwargs)
        except ProviderUnavailableError as exc:
            elapsed = time.monotonic() - start
            remaining = BUDGET_SECONDS - elapsed
            last_error = exc

            if remaining <= 0:
                break

            wait = min(exc.retry_after or default_wait, remaining)
            logger.warning(
                "Provider error (status=%s), attempt %d, waiting %.0fs (%.0fs remaining). %s",
                exc.status_code,
                attempt,
                wait,
                remaining,
                exc,
            )
            time.sleep(wait)

    elapsed = time.monotonic() - start
    raise BudgetExhaustedError(
        attempts=len(DEFAULT_BACKOFFS),
        elapsed=elapsed,
    ) from last_error


def is_retryable_status(status_code: int) -> bool:
    """Check whether an HTTP status code should trigger a retry."""
    return status_code in RETRY_STATUS_CODES
