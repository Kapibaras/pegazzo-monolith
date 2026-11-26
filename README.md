# 🚚 Pegazzo Drivers Monolith API

This repository contains the **Pegazzo Monolith API**, built with **FastAPI** and **SQLAlchemy**, designed to manage drivers efficiently.

It includes full support for database migrations, testing, and local development.

---

## 📦 Tech Stack

- ⚡ **FastAPI** – high-performance async Python web framework
- 🧱 **SQLAlchemy** – ORM and database management
- 🐍 **Pipenv** – dependency and virtual environment management
- 🛠️ **Alembic** – database migrations
- ✅ **Pytest** – testing framework
- 🥬 **Celery + Redis** – async task queue for background jobs

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Kapibaras/pegazzo-monolith.git
cd pegazzo-monolith
```

### 2. Set up your development environment

This will create a virtual environment, install dependencies, and set up a pre-commit hook:

```bash
pipenv run setup
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
ENVIRONMENT=LOCAL
DEBUG=true
DATABASE_URL=sqlite:///./dev.db
```

> [!NOTE]
> 💡 You can also use a PostgreSQL instance:
>
> ```env
> DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/pegazzo
> ```

### 4. Run the application

```bash
pipenv run dev
```

> [!NOTE]
> By default, the API is available at on all your local network:
> 👉 [http://localhost:8000](http://localhost:8000)

### 5. Run tests

```bash
pipenv run test
```

### 6. (Optional) Open a Pipenv shell

```bash
pipenv shell
```

---

## 🔧 Database Migrations with Alembic

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of change"
```

### Apply migrations

```bash
alembic upgrade head
```

### Revert the last migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

### Show current migration

```bash
alembic current
```

---

## 🥬 Async Worker (Celery + Redis)

The monolith includes a Celery worker for async background tasks (document analysis, future expiry alerts, etc.).

### Architecture

```
FastAPI API  ──enqueue──>  Redis (broker)  ──deliver──>  Celery Worker
                                                           │
                                                     PostgreSQL (results)
                                                           │
                                                     Celery Beat (periodic checks)
```

- **Queue**: `documents` (default). Add more queues as needed in `app/worker/celery_app.py`.
- **Retries**: Provider errors (503, 429, timeouts) retry with backoff ~5/15/45/90s, total budget ~3 min. See `app/worker/retry.py`.
- **Time limits**: soft=4min, hard=5min per task.
- **Stuck task check**: Beat runs every 5 min — records in `processing` longer than `WORKER_STUCK_TASK_MINUTES` (default 10) are marked `failed`.
- **Idempotency**: Tasks skip records already in terminal state (at-least-once delivery safe).

### Running locally with Docker Compose

```bash
docker compose up
```

This starts: PostgreSQL, Redis, API (port 8000), Worker, and Beat.

### Running worker manually (without Docker)

```bash
# Start Redis (must be running)
# Terminal 1 — Worker
celery -A app.worker.celery_app worker --loglevel=INFO --concurrency=2 -Q documents

# Terminal 2 — Beat (periodic tasks)
celery -A app.worker.celery_app beat --loglevel=INFO
```

### Environment variables

| Variable | Description | Default (LOCAL) |
|---|---|---|
| `CELERY_BROKER_URL` | Redis broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis result backend URL | `redis://localhost:6379/1` |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks synchronously (for tests) | `false` |
| `WORKER_STUCK_TASK_MINUTES` | Threshold for stuck task detection | `10` |

### Adding a new task

1. Create `app/worker/tasks/my_task.py`
2. Define the task using `@app.task` from `app.worker.celery_app`
3. For tasks with DB access, inherit from `BaseTask` (`app/worker/base.py`) and implement `process()`
4. The task is auto-discovered — no registration needed

### Health check

`GET /health` returns a `broker` field:
```json
{"status": "ok", "database": "ok", "broker": "ok"}
```
Broker down is **non-fatal** — the API keeps running, but the flag shows `unreachable`.

---

## 📄 Document analysis: temporary storage and promotion

Registration documents are uploaded and analyzed **before** the car, driver or associate exists. They live in a temporary area until the person saves a section of the registration; only then do they become final `Document` rows.

### Lifecycle of an analysis (`document_analysis`)

```
uploaded ──analysis (PGZ-124)──> analyzed | rejected | failed ──section saved──> consumed
uploaded ──section saved (evidence-only types, e.g. plates)──────────────────> consumed
```

1. `POST /pegazzo/management/documents/analysis/upload-url` (`OWNER`, `ADMIN`) validates the declared type, the number of files, the content types and the sizes (max 15 MB, `DocumentConfig.MAX_FILE_BYTES`), creates the row with `status = uploaded` and returns one presigned PUT per file (`Content-Type` and `Content-Length` are signed, URLs expire after 1 hour).
2. The browser PUTs the files directly to R2; the analysis endpoint (PGZ-124) fills the result columns.
3. A section endpoint calls `promote_analyses`: the files are copied to their final keys, one `Document` is created per file (linked by `document.analysis_id`) and the analysis becomes `consumed`.
4. Not consumed analyses older than **24 h** are deleted with their temporary files by the hourly beat task `cleanup-expired-analyses`. The R2 lifecycle rule (`private/tmp/` expires after 1 day) is the safety net.

An `analysis_id` is only usable by the user who created it; another user gets `404 analysis_not_found`.

### Storage keys

| Kind | Key in the documents bucket |
|---|---|
| Temporary file | `private/tmp/analysis/{analysis_id}/{index}.{ext}` |
| Final document | `private/{entity_type}/{entity_id}/{uuid}.{ext}` |

`document.url` and `document_analysis.files[].key` store keys **without** the `private/` prefix; the R2 helpers add it.

### Error codes

Errors keep the `{ "detail": "..." }` shape and add a stable `code` the frontend can rely on: `document_type_not_allowed`, `too_many_files`, `unsupported_content_type`, `empty_file`, `file_too_large`, `analysis_not_found`, `analysis_consumed`, `analysis_not_analyzed`, `analysis_file_missing`, `analysis_duplicated`, `manual_entry_requires_owner`, `manual_entry_not_allowed`.

### Calling the promotion from a section endpoint

`promote_analyses` **never commits**: it flushes in the caller's session so the section data and its documents are committed together. The section service commits, then deletes the temporary files; on any failure it rolls back and deletes the copied final files.

```python
from app.enum.crm import DocumentEntityType
from app.services.document_analysis import FinalValues, finalize_promotion, rollback_promotion

result = None
try:
    car = self.repository.save_identity(car_id, body, commit=False)  # non-committing section write
    result = self.analysis_service.promote_analyses(
        entity_type=DocumentEntityType.CAR,
        entity_id=car.id,
        analysis_ids=body.analysis_ids,
        manual_analysis_ids=body.manual_analysis_ids,  # OWNER only, failed / rejected analyses
        allowed_types={"circulation_card", "plates"},  # identity section (PGZ-183); the invoice goes in section B
        final_values={doc.analysis_id: FinalValues(fields=doc.fields, expiry_date=doc.expiry_date) for doc in body.documents},
        caller=user,
    )
    self.repository.commit()
except Exception:
    self.repository.rollback()
    if result is not None:
        rollback_promotion(result)  # removes the copied final files; temporary files stay for a retry
    raise
finalize_promotion(result)  # best effort: deletes the temporary files
```

Rules enforced by the promotion: analyzable types need `status = analyzed`; evidence-only types are promoted from `uploaded`; manual entry (`manual_analysis_ids`) requires `OWNER` and an analysis that is `failed`, or `rejected` for any reason except `wrong_document`. Analyzed documents are saved as `valid` and verified by the caller; manual and evidence-only ones as `not_analyzed` (manual ones verified by the owner).

---

## 📂 Project Structure

```txt
pegazzo-monolith/
├── .vscode/                # VSCode workspace settings
├── alembic/                # Database migration scripts
├── app/                    # Main application package
│   ├── config/             # Application configuration
│   ├── database/           # Database setup and session management
│   ├── dependencies/       # Dependency injection for FastAPI
│   ├── errors/             # Custom error handling and exceptions
│   ├── models/             # SQLAlchemy models
│   ├── repositories/       # Data access layer
│   ├── routers/            # FastAPI routers (endpoints)
│   ├── schemas/            # Pydantic schemas (request/response validation)
│   ├── services/           # Business logic layer
│   ├── utils/              # Utility functions and helpers
│   ├── worker/             # Celery worker (tasks, retries, beat schedules)
│   └── main.py             # FastAPI entrypoint
├── scripts/                # Utility or setup scripts
├── tests/                  # Test suite
├── ...
└── README.md
```
