"use client";

import { useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

import { McpUiResources } from "@/components/McpUiResources";
import type { AuthUser } from "@/services/apiClient";

interface DashboardProps {
  user: AuthUser;
  onSignOut: () => void;
}

export function Dashboard({ user, onSignOut }: DashboardProps) {
  // The dashboard widget is rendered as generative UI for the agent's
  // `get_users_overview` tool call. CopilotKit invokes this render with the
  // tool result (`result`) once the call completes; the MCP server returns the
  // widget as a single JSON envelope which McpUiResources renders in an iframe.
  useCopilotAction({
    name: "get_users_overview",
    available: "disabled",
    render: ({ status, result }) => {
      if (status === "inProgress" || status === "executing") {
        return <div className="widget-loading">Loading users overview…</div>;
      }
      return <McpUiResources result={result} />;
    },
  });

  // Same generative-UI pattern as get_users_overview, for the text-to-SQL
  // widgets: get_db_schema (schema-explorer) and run_sql_query (sql-results).
  // McpUiResources needs no per-widget changes — it renders whatever envelope
  // the mcp_server tool returned.
  useCopilotAction({
    name: "get_db_schema",
    available: "disabled",
    render: ({ status, result }) => {
      if (status === "inProgress" || status === "executing") {
        return <div className="widget-loading">Loading database schema…</div>;
      }
      return <McpUiResources result={result} />;
    },
  });

  useCopilotAction({
    name: "run_sql_query",
    available: "disabled",
    render: ({ status, result }) => {
      if (status === "inProgress" || status === "executing") {
        return <div className="widget-loading">Running query…</div>;
      }
      return <McpUiResources result={result} />;
    },
  });

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <strong>Admin Dashboard</strong>
          <span className="dashboard-user"> · {user.email}</span>
        </div>
        <button className="signout" onClick={onSignOut}>
          Sign out
        </button>
      </header>

      <main className="dashboard-main">
        <section className="dashboard-intro">
          <h2>Assistant</h2>
          <p>
            Ask the assistant to render dashboards, e.g. <em>&ldquo;show me the
            users overview&rdquo;</em>, or ask it questions about the data, e.g.
            <em>&ldquo;how many clientes are in each segmento?&rdquo;</em> or
            <em>&ldquo;show me the database schema&rdquo;</em>. Widgets are
            rendered inline in the chat, right below the assistant&rsquo;s reply.
          </p>
        </section>

        <section className="chat-panel">
          <CopilotChat
            labels={{
              title: "Admin Assistant",
              initial: "Hi! Ask me to show the users overview, or ask a question about the data.",
            }}
          />
        </section>
      </main>
    </div>
  );
}
