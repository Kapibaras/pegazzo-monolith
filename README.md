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
│   └── main.py             # FastAPI entrypoint
├── scripts/                # Utility or setup scripts
├── tests/                  # Test suite
├── ...
└── README.md
```
