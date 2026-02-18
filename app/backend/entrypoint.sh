#!/bin/sh
set -e

if [ "${APP_RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  uv run alembic upgrade head
fi

exec "$@"
