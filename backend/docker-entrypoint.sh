#!/bin/sh
# Start of the backend container (compose profile "demo"): migrate, optionally seed, serve.
set -e
alembic upgrade head
if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m scripts.seed
  python -m scripts.seed_demo
fi
# One process: background tasks, semaphores and rate-limit counters live in memory.
# --proxy-headers: behind nginx, the client address comes from X-Forwarded-For.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'
