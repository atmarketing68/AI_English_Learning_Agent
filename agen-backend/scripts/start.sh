#!/bin/sh
# AGEN Backend — Production Startup Script
# Runs Alembic migrations before starting the server.
# This ensures the DB schema is always up-to-date on every deploy.

set -e  # Exit immediately on error

echo "==> Running database migrations..."
python -m alembic upgrade head

echo "==> Starting AGEN API server..."
exec python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WORKERS:-1}" \
    --log-level info \
    --no-access-log
