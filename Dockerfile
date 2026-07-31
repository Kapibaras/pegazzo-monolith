FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv --no-cache-dir

COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --ignore-pipfile

RUN adduser --disabled-password --gecos "" appuser

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

# Required environment variables (pass at runtime via -e or --env-file):
# ENV ENVIRONMENT=PRODUCTION
# ENV DATABASE_URL=postgresql://user:pass@host:5432/dbname
# ENV JWT_SECRET_KEY=your_secret_key
# ENV JWT_ACCESS_TOKEN_EXPIRES_MIN=15
# ENV JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8000"]
