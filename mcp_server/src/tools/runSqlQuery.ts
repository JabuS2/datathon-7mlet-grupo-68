import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

import { assertAdminAuthorized } from "../apiClient.js";
import { extractAuthorization } from "../authHeader.js";
import type { Config } from "../config.js";
import { getPool, type DatabaseName } from "../db.js";
import { guardSelectStatement, ROW_CAP, STATEMENT_TIMEOUT_MS } from "../sqlGuard.js";
import { SQL_RESULTS_WIDGET_URI, buildSqlResultsHtml } from "../widgets/sqlResults.js";

const inputSchema = {
  sql: z.string().min(1).describe("A single read-only SELECT/WITH statement."),
  database: z
    .enum(["api_service", "model_service"])
    .describe("Which database to query: api_service (clientes, ofertas, decisoes, ...) or model_service (politicas, ciclos_retreino, ...)."),
  question: z.string().optional().describe("The admin's original natural-language question, shown alongside the results."),
};

async function runGuardedQuery(database: DatabaseName, config: Config, sql: string) {
  const guardedSql = guardSelectStatement(sql);
  const pool = getPool(database, config);
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query(`SET LOCAL statement_timeout = ${STATEMENT_TIMEOUT_MS}`);
    await client.query("SET TRANSACTION READ ONLY");
    const result = await client.query(guardedSql);
    await client.query("COMMIT");

    const columns = result.fields.map((f) => f.name);
    const rows = result.rows.map((row) => columns.map((c) => row[c]));
    return { columns, rows };
  } catch (error) {
    await client.query("ROLLBACK").catch(() => undefined);
    throw error;
  } finally {
    client.release();
  }
}

export function registerRunSqlQuery(server: McpServer, config: Config): void {
  server.registerTool(
    "run_sql_query",
    {
      title: "Run a read-only SQL query",
      description:
        "Run a single SELECT/WITH query against api_service or model_service and render the " +
        `result as a table widget. Read-only (enforced by both the DB role and this tool), ` +
        `capped at ${ROW_CAP} rows, ${STATEMENT_TIMEOUT_MS / 1000}s timeout. Call get_db_schema ` +
        "first if you're not certain of the exact table/column names.",
      inputSchema,
    },
    async ({ sql, database, question }, extra) => {
      const authorization = extractAuthorization(extra);
      try {
        await assertAdminAuthorized(config.apiServiceUrl, authorization);

        const { columns, rows } = await runGuardedQuery(database as DatabaseName, config, sql);

        const summary = question
          ? `Ran a query for "${question}" against ${database}: ${rows.length} row(s).`
          : `Ran a query against ${database}: ${rows.length} row(s).`;

        const widgetData = {
          database: database as DatabaseName,
          question,
          sql,
          columns,
          rows,
          rowCap: ROW_CAP,
        };

        const envelope = {
          type: "mcp_ui_widget",
          widget: "sql-results",
          uri: SQL_RESULTS_WIDGET_URI,
          mimeType: "text/html",
          html: buildSqlResultsHtml(widgetData),
          summary,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(envelope) }],
          structuredContent: { columns, rows } as unknown as Record<string, unknown>,
        };
      } catch (error) {
        console.error(
          `[mcp] run_sql_query failed: ${error instanceof Error ? error.message : String(error)}`,
        );
        throw error;
      }
    },
  );
}
