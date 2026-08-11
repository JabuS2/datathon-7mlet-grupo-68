"use client";

import { UIResourceRenderer, isUIResource } from "@mcp-ui/client";

type UnknownRecord = Record<string, unknown>;

/**
 * Self-contained widget delivered by the agent as a single JSON content block
 * (see mcp_server get_users_overview). Transported this way because the
 * AG-UI/LangGraph bridge persists only the first content block of a tool
 * message, which would otherwise drop a separately-attached MCP-UI resource.
 */
interface WidgetEnvelope {
  html: string;
  summary?: string;
  uri?: string;
}

function normalizeResult(result: unknown): unknown {
  if (typeof result !== "string") {
    return result;
  }

  try {
    return JSON.parse(result);
  } catch {
    return result;
  }
}

function looksLikeHtmlWidget(value: string): boolean {
  const trimmed = value.trim().toLowerCase();
  return (
    trimmed.startsWith("<!doctype html") ||
    trimmed.startsWith("<html") ||
    trimmed.includes("<body")
  );
}

function collectStrings(result: unknown): string[] {
  const root = normalizeResult(result);
  const found: string[] = [];
  const seen = new Set<string>();

  const push = (value: string) => {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized)) {
      return;
    }
    seen.add(normalized);
    found.push(normalized);
  };

  const visit = (value: unknown) => {
    if (!value) return;
    if (typeof value === "string") {
      push(value);
      return;
    }
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }
    if (typeof value === "object") {
      Object.values(value as UnknownRecord).forEach(visit);
    }
  };

  visit(root);
  return found;
}

/**
 * Deep-scans an agent tool result for the JSON widget envelope emitted by the
 * MCP server. This is the primary render path; the resource/HTML scanners below
 * remain as defensive fallbacks.
 */
export function findWidgetEnvelopes(result: unknown): WidgetEnvelope[] {
  const data = normalizeResult(result);
  const found: WidgetEnvelope[] = [];

  const visit = (value: unknown) => {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }
    if (typeof value === "object") {
      const record = value as UnknownRecord;
      if (record.type === "mcp_ui_widget" && typeof record.html === "string") {
        found.push({
          html: record.html,
          summary: typeof record.summary === "string" ? record.summary : undefined,
          uri: typeof record.uri === "string" ? record.uri : undefined,
        });
        return;
      }
      Object.values(record).forEach(visit);
    }
  };

  visit(data);
  return found;
}

/**
 * Deep-scans an agent tool result for MCP-UI resource blocks. The result shape
 * coming back through AG-UI is not strongly typed, so we walk it defensively.
 */
export function findUIResources(result: unknown): UnknownRecord[] {
  const data = normalizeResult(result);

  const found: UnknownRecord[] = [];
  const visit = (value: unknown) => {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }
    if (typeof value === "object") {
      if (isUIResource(value as { type: string })) {
        found.push(value as UnknownRecord);
      }
      Object.values(value as UnknownRecord).forEach(visit);
    }
  };

  visit(data);
  return found;
}

function findHtmlWidgets(result: unknown): string[] {
  return collectStrings(result).filter(looksLikeHtmlWidget);
}

export function hasRenderableMcpUiContent(result: unknown): boolean {
  return (
    findWidgetEnvelopes(result).length > 0 ||
    findUIResources(result).length > 0 ||
    findHtmlWidgets(result).length > 0
  );
}

const IFRAME_STYLE = {
  width: "100%",
  minHeight: 600,
  border: "1px solid #e5e7eb",
  borderRadius: 12,
} as const;

export function McpUiResources({ result }: { result: unknown }) {
  const envelopes = findWidgetEnvelopes(result);

  // Primary path: the structured widget envelope.
  if (envelopes.length > 0) {
    return (
      <>
        {envelopes.map((widget, index) => (
          <iframe
            key={widget.uri ? `${widget.uri}-${index}` : `widget-${index}`}
            srcDoc={widget.html}
            sandbox=""
            title={widget.summary ?? "Dashboard widget"}
            style={IFRAME_STYLE}
          />
        ))}
      </>
    );
  }

  // Fallbacks: structured MCP-UI resources or raw self-contained HTML.
  const resources = findUIResources(result);
  const htmlWidgets = findHtmlWidgets(result);

  if (resources.length === 0 && htmlWidgets.length === 0) {
    return null;
  }

  return (
    <>
      {resources.map((block, index) => (
        <UIResourceRenderer
          key={`resource-${index}`}
          resource={(block as { resource: { uri: string } }).resource}
          htmlProps={{ autoResizeIframe: true, style: { width: "100%", minHeight: 600 } }}
          onUIAction={async (action) => {
            console.log("MCP-UI action:", action);
          }}
        />
      ))}
      {htmlWidgets.map((html, index) => (
        <iframe
          key={`html-widget-${index}`}
          srcDoc={html}
          sandbox=""
          title={`users-overview-widget-${index}`}
          style={IFRAME_STYLE}
        />
      ))}
    </>
  );
}
