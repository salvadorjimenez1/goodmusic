#!/bin/sh
set -e
set -u

cd /app

printf '%s
' "Waiting for database and applying migrations..."
attempt=0
max_attempts=5

until alembic upgrade head; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    printf '%s
' "Alembic upgrade failed after $max_attempts attempts. Aborting."
    exit 1
  fi
  printf '%s
' "Alembic upgrade failed (attempt $attempt/$max_attempts). Retrying in 2s..."
  sleep 2
done

printf '%s
' "running seed data loader..."
python -m seed

printf '%s
' "Starting API server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
