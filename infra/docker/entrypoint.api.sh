#!/bin/sh
# Entrypoint for the api_service container.
#
# On startup it:
#   1. waits until Postgres accepts connections,
#   2. applies database migrations (alembic upgrade head),
#   3. seeds the database (admin + fake users) unless SEED_DB=false,
#   4. starts the API server.
#
# The seed is idempotent, so it is safe to run on every boot.
set -e

POSTGRES_SERVER="${POSTGRES_SERVER:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "Waiting for Postgres at ${POSTGRES_SERVER}:${POSTGRES_PORT} ..."
python - <<'PY'
import os
import sys
import time

import psycopg2

host = os.getenv("POSTGRES_SERVER", "postgres")
port = int(os.getenv("POSTGRES_PORT", "5432"))
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
dbname = os.getenv("POSTGRES_DB", "postgres")

for _ in range(60):
    try:
        psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        ).close()
        print("Postgres is ready.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"  Postgres not ready yet: {exc}")
        time.sleep(2)

print("ERROR: Postgres did not become ready in time.", file=sys.stderr)
sys.exit(1)
PY

echo "Applying database migrations ..."
alembic upgrade head

if [ "${SEED_DB:-true}" = "true" ]; then
  echo "Seeding database ..."
  python seed.py
else
  echo "SEED_DB=${SEED_DB} — skipping database seed."
fi

echo "Starting API server ..."
exec ddtrace-run uvicorn main:app --host 0.0.0.0 --port 8000
