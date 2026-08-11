export interface Config {
  port: number;
  mcpPath: string;
  apiServiceUrl: string;
  /** Read-only connection string for the api_service Postgres database (text-to-SQL widget). */
  readonlyDatabaseUrl?: string;
  /** Read-only connection string for the model_service Postgres database (text-to-SQL widget). */
  readonlyModelDatabaseUrl?: string;
}

export function loadConfig(): Config {
  return {
    port: Number(process.env.PORT ?? 8200),
    mcpPath: process.env.MCP_HTTP_PATH ?? "/mcp",
    apiServiceUrl: (process.env.API_SERVICE_URL ?? "http://localhost:8000").replace(/\/$/, ""),
    readonlyDatabaseUrl: process.env.READONLY_DATABASE_URL || undefined,
    readonlyModelDatabaseUrl: process.env.READONLY_MODEL_DATABASE_URL || undefined,
  };
}
