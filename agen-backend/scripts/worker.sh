#!/usr/bin/env sh
set -eu
exec celery -A app.worker:celery_app worker --loglevel=INFO --concurrency="${WORKER_CONCURRENCY:-2}"