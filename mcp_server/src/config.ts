export interface Config {
  port: number;
  mcpPath: string;
  apiServiceUrl: string;
}

export function loadConfig(): Config {
  return {
    port: Number(process.env.PORT ?? 8200),
    mcpPath: process.env.MCP_HTTP_PATH ?? "/mcp",
    apiServiceUrl: (process.env.API_SERVICE_URL ?? "http://localhost:8000").replace(/\/$/, ""),
  };
}
