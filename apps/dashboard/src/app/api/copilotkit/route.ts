import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? "http://localhost:8100/";
const AGENT_NAME = process.env.NEXT_PUBLIC_AGENT_NAME ?? "admin_dashboard_agent";

/**
 * CopilotKit runtime endpoint. It bridges the browser to the AG-UI agent
 * (agent_service). The admin JWT sent by the CopilotKit provider is forwarded
 * to the agent so it can reach the admin-only tools/data.
 */
export const POST = async (req: NextRequest) => {
  const authorization = req.headers.get("authorization") ?? "";

  const agent = new HttpAgent({
    url: AGENT_SERVICE_URL,
    headers: authorization ? { Authorization: authorization } : {},
  });

  const runtime = new CopilotRuntime({
    agents: { [AGENT_NAME]: agent },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
