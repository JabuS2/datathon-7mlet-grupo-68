import { createUIResource } from "@mcp-ui/server";

import type { DatabaseName } from "../db.js";

export const SCHEMA_EXPLORER_WIDGET_URI = "ui://mcp-server/schema-explorer";

export interface ColumnInfo {
  name: string;
  dataType: string;
  nullable: boolean;
  isPrimaryKey: boolean;
}

export interface ForeignKeyInfo {
  sourceTable: string;
  sourceColumn: string;
  targetTable: string;
  targetColumn: string;
}

export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
}

export interface DatabaseSchema {
  database: DatabaseName;
  tables: TableInfo[];
  foreignKeys: ForeignKeyInfo[];
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildDatabaseSection(schema: DatabaseSchema): string {
  const fksByTable = new Map<string, ForeignKeyInfo[]>();
  for (const fk of schema.foreignKeys) {
    const list = fksByTable.get(fk.sourceTable) ?? [];
    list.push(fk);
    fksByTable.set(fk.sourceTable, list);
  }

  const tableCards = schema.tables
    .map((table) => {
      const fks = fksByTable.get(table.name) ?? [];
      const rows = table.columns
        .map((col) => {
          const pkBadge = col.isPrimaryKey ? '<span class="badge pk">PK</span>' : "";
          const fk = fks.find((f) => f.sourceColumn === col.name);
          const fkBadge = fk
            ? `<span class="badge fk">FK → ${escapeHtml(fk.targetTable)}.${escapeHtml(fk.targetColumn)}</span>`
            : "";
          const nullBadge = col.nullable ? "" : '<span class="badge nn">not null</span>';
          return `<tr><td class="colname">${escapeHtml(col.name)}</td><td class="coltype">${escapeHtml(col.dataType)}</td><td>${pkBadge}${fkBadge}${nullBadge}</td></tr>`;
        })
        .join("");
      return `<div class="table-card">
        <div class="table-name">${escapeHtml(table.name)}</div>
        <table><tbody>${rows}</tbody></table>
      </div>`;
    })
    .join("");

  return `<section class="db-section db-${escapeHtml(schema.database)}">
    <h3>${escapeHtml(schema.database)} <span class="table-count">${schema.tables.length} tables</span></h3>
    <div class="table-grid">${tableCards || "<p>No tables found.</p>"}</div>
  </section>`;
}

/**
 * Renders both databases' table/column structure as a self-contained HTML
 * string, mirroring the style of `usersOverview.ts`'s widget.
 */
export function buildSchemaExplorerHtml(schemas: DatabaseSchema[]): string {
  const sections = schemas.map(buildDatabaseSection).join("");

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 16px; background: transparent; color: #111827; }
  h2 { margin: 0 0 4px; font-size: 16px; }
  h3 { margin: 20px 0 10px; font-size: 14px; display: flex; align-items: baseline; gap: 8px; }
  .table-count { font-size: 11px; font-weight: 400; color: #6b7280; }
  .table-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
  .table-card { background: #f3f4f6; border-radius: 10px; padding: 10px 12px; }
  .table-name { font-weight: 700; font-size: 13px; margin-bottom: 6px; font-family: ui-monospace, Menlo, monospace; }
  table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
  td { padding: 3px 4px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .colname { font-family: ui-monospace, Menlo, monospace; white-space: nowrap; }
  .coltype { color: #6b7280; white-space: nowrap; }
  .badge { display: inline-block; padding: 1px 6px; border-radius: 999px; background: #e5e7eb; font-size: 9.5px; font-weight: 600; margin-right: 3px; white-space: nowrap; }
  .badge.pk { background: #dbeafe; color: #1d4ed8; }
  .badge.fk { background: #dcfce7; color: #15803d; }
  .badge.nn { background: transparent; color: #9ca3af; font-weight: 400; }
  .db-model_service h3 { color: #b8720a; }
  .db-api_service h3 { color: #1d4ed8; }
  @media (prefers-color-scheme: dark) {
    body { color: #e5e7eb; }
    .table-card { background: #1f2937; }
    .table-count { color: #9ca3af; }
    .coltype { color: #9ca3af; }
    td { border-color: #374151; }
    .badge { background: #374151; }
    .badge.pk { background: #1e3a8a; color: #bfdbfe; }
    .badge.fk { background: #14532d; color: #bbf7d0; }
    .db-model_service h3 { color: #fbbf24; }
    .db-api_service h3 { color: #93c5fd; }
  }
</style>
</head>
<body>
  <h2>Database Schema</h2>
  ${sections}
</body>
</html>`;
}

export function buildSchemaExplorerWidget(schemas: DatabaseSchema[]) {
  return createUIResource({
    uri: SCHEMA_EXPLORER_WIDGET_URI,
    content: { type: "rawHtml", htmlString: buildSchemaExplorerHtml(schemas) },
    encoding: "text",
  });
}
