import express from "express";

import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

import { loadConfig } from "./config.js";
import { createMcpServer } from "./server.js";

const config = loadConfig();
const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// Stateless streamable-HTTP MCP endpoint. A new server + transport is created
// per request so that per-request headers (the admin JWT) stay isolated.
app.post(config.mcpPath, async (req, res) => {
  const hasAuth = Boolean(req.headers["authorization"]);
  console.log(
    `[mcp] POST ${config.mcpPath} auth=${hasAuth ? "present" : "missing"}`,
  );

  const server = createMcpServer(config);
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  res.on("close", () => {
    void transport.close();
    void server.close();
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("Error handling MCP request:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal server error" },
        id: null,
      });
    }
  }
});

// GET/DELETE are not supported in stateless mode.
const methodNotAllowed = (_req: express.Request, res: express.Response) => {
  res.status(405).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Method not allowed." },
    id: null,
  });
};
app.get(config.mcpPath, methodNotAllowed);
app.delete(config.mcpPath, methodNotAllowed);

app.listen(config.port, () => {
  console.log(`MCP server listening on http://localhost:${config.port}${config.mcpPath}`);
  console.log(`Proxying admin data from ${config.apiServiceUrl}`);
});
