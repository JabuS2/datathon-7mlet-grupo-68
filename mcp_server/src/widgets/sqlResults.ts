import { createUIResource } from "@mcp-ui/server";

import type { DatabaseName } from "../db.js";

export const SQL_RESULTS_WIDGET_URI = "ui://mcp-server/sql-results";

export interface SqlResultsData {
  database: DatabaseName;
  question?: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  rowCap: number;
}

function escapeHtml(value: string): string {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '<span class="null">null</span>';
  if (typeof value === "object") return escapeHtml(JSON.stringify(value));
  return escapeHtml(String(value));
}

/**
 * Renders a SQL query + its result set as a self-contained HTML string,
 * mirroring the style of `usersOverview.ts`'s widget.
 */
export function buildSqlResultsHtml(data: SqlResultsData): string {
  const headerRow = data.columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const bodyRows = data.rows
    .map((row) => `<tr>${row.map((cell) => `<td>${formatCell(cell)}</td>`).join("")}</tr>`)
    .join("");

  const truncatedNote =
    data.rows.length >= data.rowCap
      ? `<p class="note">Showing the first ${data.rowCap} rows — results may be truncated.</p>`
      : "";

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 16px; background: transparent; color: #111827; }
  h2 { margin: 0 0 4px; font-size: 16px; }
  .question { font-size: 13px; color: #4b5563; margin: 0 0 10px; }
  .sql { background: #f3f4f6; border-radius: 8px; padding: 10px 12px; font-family: ui-monospace, Menlo, monospace; font-size: 12px; white-space: pre-wrap; word-break: break-word; margin-bottom: 12px; }
  .db-tag { display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 10.5px; font-weight: 600; margin-bottom: 8px; }
  .db-tag.api_service { background: #dbeafe; color: #1d4ed8; }
  .db-tag.model_service { background: #fef3c7; color: #b8720a; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }
  th { color: #6b7280; font-weight: 600; position: sticky; top: 0; background: inherit; }
  .null { color: #9ca3af; font-style: italic; }
  .note { font-size: 11.5px; color: #9ca3af; margin-top: 8px; }
  @media (prefers-color-scheme: dark) {
    body { color: #e5e7eb; }
    .question { color: #9ca3af; }
    .sql { background: #1f2937; }
    .db-tag.api_service { background: #1e3a8a; color: #bfdbfe; }
    .db-tag.model_service { background: #451a03; color: #fbbf24; }
    th, td { border-color: #374151; }
    th { color: #9ca3af; }
  }
</style>
</head>
<body>
  <h2>SQL Results</h2>
  <span class="db-tag ${escapeHtml(data.database)}">${escapeHtml(data.database)}</span>
  ${data.question ? `<p class="question">${escapeHtml(data.question)}</p>` : ""}
  <div class="sql">${escapeHtml(data.sql)}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>${headerRow}</tr></thead>
      <tbody>${bodyRows || `<tr><td colspan="${data.columns.length || 1}">No rows returned.</td></tr>`}</tbody>
    </table>
  </div>
  ${truncatedNote}
</body>
</html>`;
}

export function buildSqlResultsWidget(data: SqlResultsData) {
  return createUIResource({
    uri: SQL_RESULTS_WIDGET_URI,
    content: { type: "rawHtml", htmlString: buildSqlResultsHtml(data) },
    encoding: "text",
  });
}
