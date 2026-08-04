#!/bin/bash
# Cria o database do model_service ao inicializar o Postgres.
#
# O model_service tem cadeia Alembic PRÓPRIA. Duas cadeias no mesmo database disputariam a
# tabela `alembic_version` — a segunda a rodar `upgrade head` encontraria uma revisão que
# não conhece. Mesma instância, databases separados.
#
# Roda uma vez só, na criação do volume `postgres_data` (comportamento do
# /docker-entrypoint-initdb.d). Num volume que já existe, crie à mão:
#   docker compose exec postgres createdb -U "$POSTGRES_USER" model_service
set -e

MODEL_DB="${MODEL_POSTGRES_DB:-model_service}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE $MODEL_DB'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$MODEL_DB')\gexec
EOSQL

echo "Database '$MODEL_DB' pronto para o model_service."
