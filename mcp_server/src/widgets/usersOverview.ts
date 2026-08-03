import { createUIResource } from "@mcp-ui/server";

import type { UsersOverview } from "../apiClient.js";

export const USERS_OVERVIEW_WIDGET_URI = "ui://mcp-server/users-overview";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Renders the fully self-contained users-overview dashboard as an HTML string.
 * The data is embedded inline so the sandboxed iframe makes no external calls
 * and needs no scripts.
 */
export function buildUsersOverviewHtml(data: UsersOverview): string {
  const rows = data.latestUsers
    .map((user) => {
      const created = user.createdAt ? new Date(user.createdAt).toLocaleString() : "—";
      const badge = user.isAdmin
        ? '<span class="badge admin">admin</span>'
        : '<span class="badge">user</span>';
      return `<tr><td>${escapeHtml(user.email)}</td><td>${badge}</td><td>${escapeHtml(created)}</td></tr>`;
    })
    .join("");

  const card = (label: string, value: number) =>
    `<div class="kpi"><div class="kpi-value">${value}</div><div class="kpi-label">${label}</div></div>`;

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 16px; background: transparent; color: #111827; }
  h2 { margin: 0 0 12px; font-size: 16px; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .kpi { background: #f3f4f6; border-radius: 12px; padding: 14px; text-align: center; }
  .kpi-value { font-size: 26px; font-weight: 700; }
  .kpi-label { font-size: 12px; color: #6b7280; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #e5e7eb; }
  th { color: #6b7280; font-weight: 600; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e5e7eb; font-size: 11px; }
  .badge.admin { background: #dbeafe; color: #1d4ed8; }
  @media (prefers-color-scheme: dark) {
    body { color: #e5e7eb; }
    .kpi { background: #1f2937; }
    .kpi-label, th { color: #9ca3af; }
    th, td { border-color: #374151; }
    .badge { background: #374151; }
    .badge.admin { background: #1e3a8a; color: #bfdbfe; }
  }
</style>
</head>
<body>
  <h2>Admin Users Overview</h2>
  <div class="kpis">
    ${card("Total users", data.totalUsers)}
    ${card("Admins", data.adminCount)}
    ${card("Signups (7d)", data.signupsLast7Days)}
    ${card("Signups (30d)", data.signupsLast30Days)}
  </div>
  <table>
    <thead><tr><th>Email</th><th>Role</th><th>Created</th></tr></thead>
    <tbody>${rows || '<tr><td colspan="3">No users yet</td></tr>'}</tbody>
  </table>
</body>
</html>`;
}

/**
 * Builds an MCP-UI resource (mcpApp widget) that renders the users overview
 * dashboard. The data is embedded into the HTML so the sandboxed iframe is
 * fully self-contained and makes no external calls.
 */
export function buildUsersOverviewWidget(data: UsersOverview) {
  return createUIResource({
    uri: USERS_OVERVIEW_WIDGET_URI,
    content: { type: "rawHtml", htmlString: buildUsersOverviewHtml(data) },
    encoding: "text",
  });
}
