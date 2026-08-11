import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import type { Config } from "./config.js";
import { registerGetUsersOverview } from "./tools/getUsersOverview.js";
import { registerGetDbSchema } from "./tools/getDbSchema.js";
import { registerRunSqlQuery } from "./tools/runSqlQuery.js";

/**
 * Creates a fresh MCP server with all tools/widgets registered. A new instance
 * is created per request to keep the streamable-HTTP transport stateless.
 */
export function createMcpServer(config: Config): McpServer {
  const server = new McpServer({
    name: "mcp-server",
    version: "0.1.0",
  });

  registerGetUsersOverview(server, config);
  registerGetDbSchema(server, config);
  registerRunSqlQuery(server, config);

  return server;
}
