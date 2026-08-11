import { buildUsersOverviewWidget } from "./usersOverview.js";
import { buildSchemaExplorerWidget } from "./schemaExplorer.js";
import { buildSqlResultsWidget } from "./sqlResults.js";

/**
 * Registry of available mcpApp widgets. Add new widget builders here as the
 * dashboard grows; each entry maps a stable id to its builder function.
 */
export const widgetRegistry = {
  "users-overview": buildUsersOverviewWidget,
  "schema-explorer": buildSchemaExplorerWidget,
  "sql-results": buildSqlResultsWidget,
} as const;

export type WidgetId = keyof typeof widgetRegistry;
