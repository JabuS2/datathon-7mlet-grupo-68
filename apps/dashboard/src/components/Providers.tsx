"use client";

import { CopilotKit } from "@copilotkit/react-core";

import { AGENT_NAME } from "@/lib/env";

export function Providers({
  token,
  children,
}: {
  token: string;
  children: React.ReactNode;
}) {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent={AGENT_NAME}
      headers={{ Authorization: `Bearer ${token}` }}
    >
      {children}
    </CopilotKit>
  );
}
