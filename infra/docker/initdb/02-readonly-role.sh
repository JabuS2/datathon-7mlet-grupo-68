#!/bin/bash
# Cria a role somente-leitura usada pelo mcp_server para o assistente de texto-para-SQL.
#
# `readonly_reporting` só tem CONNECT/USAGE/SELECT — nas duas databases (a do api_service e a
# do model_service) e em qualquer tabela futura (via ALTER DEFAULT PRIVILEGES). É o limite
# físico: mesmo que o agente LLM seja enganado por um prompt malicioso, esta role não tem
# INSERT/UPDATE/DELETE/DDL para executar — a proteção não depende da validação da query em
# código, é a própria permissão no Postgres.
#
# Roda uma vez só, na criação do volume `postgres_data` (mesma ressalva do script 01: num
# volume que já existe, aplique manualmente via `docker compose exec postgres psql ...`).
set -e

MODEL_DB="${MODEL_POSTGRES_DB:-model_service}"
READONLY_USER="${READONLY_DB_USER:-readonly_reporting}"

if [ -z "${READONLY_DB_PASSWORD:-}" ]; then
    echo "READONLY_DB_PASSWORD não definido — pulando criação de '$READONLY_USER' (defina no .env para habilitar o assistente de texto-para-SQL)."
    exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$READONLY_USER') THEN
            EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '$READONLY_USER', '$READONLY_DB_PASSWORD');
        END IF;
    END
    \$\$;

    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$READONLY_USER";
    GRANT CONNECT ON DATABASE "$MODEL_DB" TO "$READONLY_USER";
EOSQL

# GRANT/ALTER DEFAULT PRIVILEGES are per-database, so connect to each in turn. Default
# privileges are scoped "FOR ROLE $POSTGRES_USER" because that's the role Alembic runs
# migrations as in both services — new tables it creates automatically become readable.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO "$READONLY_USER";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "$READONLY_USER";
    ALTER DEFAULT PRIVILEGES FOR ROLE "$POSTGRES_USER" IN SCHEMA public
        GRANT SELECT ON TABLES TO "$READONLY_USER";
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$MODEL_DB" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO "$READONLY_USER";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "$READONLY_USER";
    ALTER DEFAULT PRIVILEGES FOR ROLE "$POSTGRES_USER" IN SCHEMA public
        GRANT SELECT ON TABLES TO "$READONLY_USER";
EOSQL

echo "Role '$READONLY_USER' pronta (SELECT-only em '$POSTGRES_DB' e '$MODEL_DB')."
