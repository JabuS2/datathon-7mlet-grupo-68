/**
 * Pulls the forwarded `Authorization` header out of an MCP tool call's
 * request info. Shared by every tool that needs to forward (or check) the
 * caller's admin JWT — see `agent_service`'s `AuthForwardingInterceptor`,
 * which is what attaches this header on the way in.
 */
export function extractAuthorization(extra: unknown): string | undefined {
  const headers = (
    extra as { requestInfo?: { headers?: Record<string, string | string[] | undefined> } }
  )?.requestInfo?.headers;
  if (!headers) return undefined;

  const raw = headers["authorization"] ?? headers["Authorization"];
  return Array.isArray(raw) ? raw[0] : raw;
}
