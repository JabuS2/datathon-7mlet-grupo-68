import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import { extractAuthorization } from "../authHeader.js";
import { fetchUsersOverview } from "../apiClient.js";
import type { Config } from "../config.js";
import {
  USERS_OVERVIEW_WIDGET_URI,
  buildUsersOverviewHtml,
} from "../widgets/usersOverview.js";

export function registerGetUsersOverview(server: McpServer, config: Config): void {
  server.registerTool(
    "get_users_overview",
    {
      title: "Get users overview",
      description:
        "Fetch admin KPIs (total users, admin count, recent signups, latest users) " +
        "and render them as an interactive dashboard widget for the admin.",
      inputSchema: {},
    },
    async (_args, extra) => {
      const authorization = extractAuthorization(extra);
      console.log(
        `[mcp] get_users_overview called auth=${authorization ? "present" : "missing"}`,
      );
      try {
        const data = await fetchUsersOverview(config.apiServiceUrl, authorization);
        console.log(
          `[mcp] get_users_overview ok totalUsers=${data.totalUsers} adminCount=${data.adminCount}`,
        );

        const summary =
          `Users overview: ${data.totalUsers} total users, ${data.adminCount} admins, ` +
          `${data.signupsLast7Days} signups in the last 7 days, ` +
          `${data.signupsLast30Days} in the last 30 days.`;

        // Return the widget as a SINGLE text content block carrying a JSON
        // envelope. The AG-UI/LangGraph bridge (ag_ui_langgraph
        // resolve_message_content) persists only the FIRST text block of a tool
        // message, so multi-block results silently drop the widget. Keeping one
        // deterministic block lets the frontend parse and render it reliably.
        const envelope = {
          type: "mcp_ui_widget",
          widget: "users-overview",
          uri: USERS_OVERVIEW_WIDGET_URI,
          mimeType: "text/html",
          html: buildUsersOverviewHtml(data),
          summary,
        };

        return {
          content: [{ type: "text", text: JSON.stringify(envelope) }],
          structuredContent: data as unknown as Record<string, unknown>,
        };
      } catch (error) {
        console.error(
          `[mcp] get_users_overview failed: ${error instanceof Error ? error.message : String(error)}`,
        );
        throw error;
      }
    },
  );
}
