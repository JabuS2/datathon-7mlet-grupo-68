#!/bin/sh
# Entrypoint do model_service.
#
#   1. espera o Postgres (banco próprio: governança),
#   2. aplica as migrações Alembic do model_service,
#   3. sobe o servidor sob ddtrace-run.
#
# O estado dos bandits fica no Redis, não aqui — o banco guarda só políticas, ciclos de
# retreino, aprovações e as métricas publicadas pelo api_service.
set -e

POSTGRES_SERVER="${POSTGRES_SERVER:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
MODEL_POSTGRES_DB="${MODEL_POSTGRES_DB:-model_service}"

echo "Waiting for Postgres at ${POSTGRES_SERVER}:${POSTGRES_PORT}/${MODEL_POSTGRES_DB} ..."
python - <<'PY'
import os
import sys
import time

import psycopg2

host = os.getenv("POSTGRES_SERVER", "postgres")
port = int(os.getenv("POSTGRES_PORT", "5432"))
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
dbname = os.getenv("MODEL_POSTGRES_DB", "model_service")

for _ in range(60):
    try:
        psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        ).close()
        print("Postgres is ready.")
        sys.exit(0)
    except Exception as exc:
        print(f"  Postgres not ready yet: {exc}")
        time.sleep(2)

print("ERROR: Postgres did not become ready in time.", file=sys.stderr)
sys.exit(1)
PY

echo "Applying model_service migrations ..."
alembic upgrade head

echo "Starting model service ..."
exec ddtrace-run uvicorn main:app --host 0.0.0.0 --port 8000
