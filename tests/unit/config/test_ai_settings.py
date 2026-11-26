import importlib

import pytest

from app.config import variables

AI_ENV_VARS = (
    "GOOGLE_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_TIMEOUT_SECONDS",
    "AI_MAX_DOCUMENT_BYTES",
    "AI_RETRY_BUDGET_SECONDS",
)
FAKE_KEY = "fake-google-api-key-for-tests"


@pytest.fixture
def load_ai(monkeypatch):
    """Reload the settings module with a controlled env (ignoring any local .env) and restore it afterwards."""
    monkeypatch.setattr("dotenv.load_dotenv", lambda *_args, **_kwargs: None)
    for name in AI_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    def _load(environment: str = "LOCAL", **env: str):
        monkeypatch.setenv("ENVIRONMENT", environment)
        if environment != "LOCAL":
            # Unrelated required settings, so the reload itself does not fail outside LOCAL.
            monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
            monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
            monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
            monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(variables).AI

    yield _load
    monkeypatch.undo()
    importlib.reload(variables)


def test_defaults(load_ai):
    ai = load_ai()

    assert ai.GOOGLE_API_KEY == ""
    assert ai.GEMINI_MODEL == "gemini-3.6-flash"
    assert ai.GEMINI_TIMEOUT_SECONDS == 20
    assert ai.MAX_DOCUMENT_BYTES == 15 * 1024 * 1024
    assert ai.RETRY_BUDGET_SECONDS == 20
    ai.validate()


def test_override_by_env(load_ai):
    ai = load_ai(
        GOOGLE_API_KEY=FAKE_KEY,
        GEMINI_MODEL="gemini-other",
        GEMINI_TIMEOUT_SECONDS="7.5",
        AI_MAX_DOCUMENT_BYTES="2048",
        AI_RETRY_BUDGET_SECONDS="30",
    )

    assert ai.GOOGLE_API_KEY == FAKE_KEY
    assert ai.GEMINI_MODEL == "gemini-other"
    assert ai.GEMINI_TIMEOUT_SECONDS == 7.5
    assert ai.MAX_DOCUMENT_BYTES == 2048
    assert ai.RETRY_BUDGET_SECONDS == 30
    ai.validate()


def test_validate_does_not_require_key_in_local(load_ai):
    load_ai().validate()


def test_validate_requires_key_outside_local(load_ai):
    ai = load_ai(environment="PRODUCTION")

    with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
        ai.validate()


def test_validate_passes_outside_local_with_key(load_ai):
    load_ai(environment="STAGING", GOOGLE_API_KEY=FAKE_KEY).validate()


@pytest.mark.parametrize("timeout", ["0", "-1"])
def test_validate_rejects_non_positive_timeout(load_ai, timeout):
    ai = load_ai(GOOGLE_API_KEY=FAKE_KEY, GEMINI_TIMEOUT_SECONDS=timeout)

    with pytest.raises(ValueError, match="GEMINI_TIMEOUT_SECONDS must be > 0") as exc:
        ai.validate()
    assert FAKE_KEY not in str(exc.value)


def test_validate_rejects_budget_lower_than_timeout(load_ai):
    ai = load_ai(GOOGLE_API_KEY=FAKE_KEY, GEMINI_TIMEOUT_SECONDS="15", AI_RETRY_BUDGET_SECONDS="10")

    with pytest.raises(ValueError, match="AI_RETRY_BUDGET_SECONDS") as exc:
        ai.validate()
    assert FAKE_KEY not in str(exc.value)


def test_validate_accepts_budget_equal_to_timeout(load_ai):
    load_ai(GEMINI_TIMEOUT_SECONDS="20", AI_RETRY_BUDGET_SECONDS="20").validate()


@pytest.mark.parametrize("size", ["0", "-5"])
def test_validate_rejects_non_positive_max_document_bytes(load_ai, size):
    ai = load_ai(GOOGLE_API_KEY=FAKE_KEY, AI_MAX_DOCUMENT_BYTES=size)

    with pytest.raises(ValueError, match="AI_MAX_DOCUMENT_BYTES must be > 0") as exc:
        ai.validate()
    assert FAKE_KEY not in str(exc.value)


def test_key_not_exposed_in_repr_or_str(load_ai):
    ai = load_ai(GOOGLE_API_KEY=FAKE_KEY)

    assert FAKE_KEY not in repr(ai)
    assert FAKE_KEY not in str(ai)
