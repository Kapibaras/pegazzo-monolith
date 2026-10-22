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
