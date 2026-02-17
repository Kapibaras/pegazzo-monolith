# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pegazzo Drivers Monolith API is a FastAPI-based application for managing drivers. It uses SQLAlchemy for ORM, Pipenv for dependency management, Alembic for database migrations, and Pytest for testing.

## Development Commands

### Environment Setup
```bash
pipenv run setup              # Install dependencies, set up pre-commit hooks, and clean environment
pipenv shell                  # Activate virtual environment
```

### Running the Application
```bash
pipenv run dev                # Start development server on http://0.0.0.0:8000 with auto-reload
```

### Testing
```bash
pipenv run test               # Run full test suite with coverage (requires ≥80% coverage)
pytest tests/unit/            # Run only unit tests
pytest tests/unit/test_specific.py  # Run a specific test file
pytest tests/unit/test_specific.py::test_function  # Run a specific test
```

### Linting
```bash
ruff check .                  # Check for linting issues
ruff check . --fix            # Auto-fix linting issues
ruff format .                 # Format code
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"  # Create new migration
alembic upgrade head                              # Apply all pending migrations
alembic downgrade -1                              # Revert last migration
alembic history                                   # View migration history
alembic current                                   # Show current migration
pipenv run seeders                                # Run database seeders
```

## Architecture

### Layered Architecture Pattern

The application follows a strict layered architecture:

**Routers → Services → Repositories → Models**

- **Routers** (`app/routers/`): Handle HTTP requests/responses, parameter validation, dependency injection. Must not contain business logic.
- **Services** (`app/services/`): Contain all business logic, orchestrate repository calls, handle domain exceptions.
- **Repositories** (`app/repositories/`): Data access layer, database operations only. All repositories inherit from `DBRepository` abstract base class.
- **Models** (`app/models/`): SQLAlchemy ORM models defining database schema.
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation.

### Dependency Injection

The application uses factory classes for dependency injection:

- **`RepositoryFactory`** (`app/dependencies/repository_factory.py`): Provides repository instances with database sessions injected via `get_db` dependency.
- **`ServiceFactory`** (`app/dependencies/service_factory.py`): Provides service instances with repositories and other dependencies injected.

Routers use these factories via FastAPI's `Depends`:
```python
service: UserService = Depends(ServiceFactory.user_service)
```

### Authentication & Authorization

- JWT-based authentication using `fastapi-jwt-auth-compat` library
- Configuration in `app/auth/core.py` (cookie-based tokens with CSRF protection)
- Protected routes use `RequiresAuth` dependency with role-based access control
- Roles defined in `app/enum/auth.py`
- Auth utilities in `app/utils/auth.py` for password hashing (Argon2) and verification
- `AuthUser` type represents authenticated user context

### Error Handling

Custom exceptions are organized by domain in `app/errors/`:
- `auth.py` - Authentication errors
- `user.py` - User management errors
- `balance.py` - Balance/transaction errors
- `database.py` - Database operation errors

Services should raise domain-specific exceptions, not generic ones.

### Database

- Session management via `app/database/dependency.py` (`get_db` generator)
- Database connection configured in `app/database/core.py`
- Supports both SQLite (development) and PostgreSQL (production)
- Base declarative model in `app/database/base.py`

## Code Quality Standards

### Pre-commit Hooks

All commits are validated by pre-commit hooks:
- **Conventional commits** format required (e.g., `feat:`, `fix:`, `chore:`)
- **Ruff** linting and formatting (auto-fixes applied)
- **Coverage enforcement**: Tests must maintain ≥80% coverage
- File format checks (JSON, YAML, TOML)
- No large files, merge conflicts, or private keys allowed

### Testing

- Tests use mocked repositories (`tests/mocks/`) instead of real database
- Two test client fixtures available:
  - `client`: Unauthenticated client
  - `authorized_client`: Pre-authenticated as owner role with JWT cookies
- Test state is reset between tests via `reset_state` fixture
- Repository overrides configured in `conftest.py`

## Important Patterns

### Adding a New Feature

When adding a new feature (e.g., a new entity):

1. **Model**: Create SQLAlchemy model in `app/models/`
2. **Schema**: Create Pydantic schemas in `app/schemas/`
3. **Repository**: Create repository in `app/repositories/`, inherit from `DBRepository`
4. **Service**: Create service in `app/services/` with business logic
5. **Router**: Create router in `app/routers/` with endpoint definitions
6. **Dependencies**: Add factory methods to `RepositoryFactory` and `ServiceFactory`
7. **Register Router**: Import and include router in `app/main.py`
8. **Migration**: Generate Alembic migration with `alembic revision --autogenerate`
9. **Tests**: Add unit tests in `tests/unit/` with mocked repository

### Environment Variables

Required variables (see `.env.example`):
- `ENVIRONMENT`: LOCAL, STAGING, or PRODUCTION
- `DEBUG`: Enable/disable debug mode
- `DATABASE_URL`: Database connection string (SQLite or PostgreSQL)
- `JWT_SECRET_KEY`: Secret for JWT signing (configured via AUTHORIZATION object)

## Deployment

The application is AWS Lambda-ready via Mangum handler (`handler` in `app/main.py`).
