FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv --no-cache-dir

COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

COPY . .

# Required environment variables (pass at runtime via -e or --env-file):
# ENV ENVIRONMENT=PRODUCTION
# ENV DATABASE_URL=postgresql://user:pass@host:5432/dbname
# ENV JWT_SECRET_KEY=your_secret_key
# ENV JWT_ACCESS_TOKEN_EXPIRES_MIN=15
# ENV JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
