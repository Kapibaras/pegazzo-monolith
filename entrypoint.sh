#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
