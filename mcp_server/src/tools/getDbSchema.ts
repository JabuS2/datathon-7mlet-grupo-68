import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import { assertAdminAuthorized } from "../apiClient.js";
import { extractAuthorization } from "../authHeader.js";
import type { Config } from "../config.js";
import { getPool, type DatabaseName } from "../db.js";
import {
  SCHEMA_EXPLORER_WIDGET_URI,
  buildSchemaExplorerHtml,
  type ColumnInfo,
  type DatabaseSchema,
  type ForeignKeyInfo,
} from "../widgets/schemaExplorer.js";

const COLUMNS_QUERY = `
  SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable = 'YES' AS nullable,
    EXISTS (
      SELECT 1
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
      WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_schema = 'public'
        AND kcu.table_name = c.table_name
        AND kcu.column_name = c.column_name
    ) AS is_primary_key
  FROM information_schema.columns c
  JOIN information_schema.tables t
    ON t.table_schema = c.table_schema AND t.table_name = c.table_name
  WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
  ORDER BY c.table_name, c.ordinal_position;
`;

const FOREIGN_KEYS_QUERY = `
  SELECT
    tc.table_name AS source_table,
    kcu.column_name AS source_column,
    ccu.table_name AS target_table,
    ccu.column_name AS target_column
  FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
  JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
  WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
  ORDER BY tc.table_name;
`;

async function introspect(database: DatabaseName, config: Config): Promise<DatabaseSchema> {
  const pool = getPool(database, config);

  const [columnsResult, fksResult] = await Promise.all([
    pool.query<{
      table_name: string;
      column_name: string;
      data_type: string;
      nullable: boolean;
      is_primary_key: boolean;
    }>(COLUMNS_QUERY),
    pool.query<{
      source_table: string;
      source_column: string;
      target_table: string;
      target_column: string;
    }>(FOREIGN_KEYS_QUERY),
  ]);

  const tablesByName = new Map<string, ColumnInfo[]>();
  for (const row of columnsResult.rows) {
    const columns = tablesByName.get(row.table_name) ?? [];
    columns.push({
      name: row.column_name,
      dataType: row.data_type,
      nullable: row.nullable,
      isPrimaryKey: row.is_primary_key,
    });
    tablesByName.set(row.table_name, columns);
  }

  const foreignKeys: ForeignKeyInfo[] = fksResult.rows.map((row) => ({
    sourceTable: row.source_table,
    sourceColumn: row.source_column,
    targetTable: row.target_table,
    targetColumn: row.target_column,
  }));

  return {
    database,
    tables: Array.from(tablesByName.entries()).map(([name, columns]) => ({ name, columns })),
    foreignKeys,
  };
}

export function registerGetDbSchema(server: McpServer, config: Config): void {
  server.registerTool(
    "get_db_schema",
    {
      title: "Get database schema",
      description:
        "Introspect the platform's two Postgres databases (api_service and model_service) " +
        "and render their tables, columns and foreign keys as an interactive schema widget. " +
        "Call this before writing SQL with run_sql_query if you don't already know the exact " +
        "table/column names involved.",
      inputSchema: {},
    },
    async (_args, extra) => {
      const authorization = extractAuthorization(extra);
      try {
        await assertAdminAuthorized(config.apiServiceUrl, authorization);

        const schemas = await Promise.all([
          introspect("api_service", config),
          introspect("model_service", config),
        ]);

        const totalTables = schemas.reduce((sum, s) => sum + s.tables.length, 0);
        const summary = `Database schema: ${totalTables} tables across api_service and model_service.`;

        const envelope = {
          type: "mcp_ui_widget",
          widget: "schema-explorer",
          uri: SCHEMA_EXPLORER_WIDGET_URI,
          mimeType: "text/html",
          html: buildSchemaExplorerHtml(schemas),
          summary,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(envelope) }],
          structuredContent: { schemas } as unknown as Record<string, unknown>,
        };
      } catch (error) {
        console.error(
          `[mcp] get_db_schema failed: ${error instanceof Error ? error.message : String(error)}`,
        );
        throw error;
      }
    },
  );
}
