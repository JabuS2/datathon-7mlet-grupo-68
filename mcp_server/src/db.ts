import { Pool } from "pg";

import type { Config } from "./config.js";

export type DatabaseName = "api_service" | "model_service";

const pools = new Map<DatabaseName, Pool>();

function connectionStringFor(database: DatabaseName, config: Config): string {
  const url =
    database === "api_service" ? config.readonlyDatabaseUrl : config.readonlyModelDatabaseUrl;
  if (!url) {
    const envVar = database === "api_service" ? "READONLY_DATABASE_URL" : "READONLY_MODEL_DATABASE_URL";
    throw new Error(
      `Read-only access to the '${database}' database is not configured. Set ${envVar} ` +
        "(see infra/docker/initdb/02-readonly-role.sh) to enable the text-to-SQL tools.",
    );
  }
  return url;
}

/**
 * Lazily-created, per-database connection pool using the SELECT-only
 * `readonly_reporting` Postgres role. One pool per database name, reused
 * across MCP requests (unlike the McpServer instance, which is per-request).
 */
export function getPool(database: DatabaseName, config: Config): Pool {
  const existing = pools.get(database);
  if (existing) return existing;

  const pool = new Pool({ connectionString: connectionStringFor(database, config), max: 4 });
  pools.set(database, pool);
  return pool;
}
