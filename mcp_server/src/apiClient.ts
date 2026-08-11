export interface UserSummary {
  email: string;
  isAdmin: boolean;
  createdAt: string | null;
}

export interface UsersOverview {
  totalUsers: number;
  adminCount: number;
  signupsLast7Days: number;
  signupsLast30Days: number;
  latestUsers: UserSummary[];
}

/**
 * Calls the api_service admin endpoint. The admin JWT is forwarded from the
 * incoming MCP request so access control is enforced by api_service itself.
 */
export async function fetchUsersOverview(
  apiServiceUrl: string,
  authorization: string | undefined,
): Promise<UsersOverview> {
  if (!authorization) {
    throw new Error("Missing Authorization header: an admin JWT is required.");
  }

  const response = await fetch(`${apiServiceUrl}/api/v1/admin/users/overview`, {
    method: "GET",
    headers: {
      Authorization: authorization,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `api_service returned ${response.status} for users overview: ${body.slice(0, 200)}`,
    );
  }

  return (await response.json()) as UsersOverview;
}

/**
 * Confirms the forwarded JWT belongs to an admin, without needing the payload.
 * Reuses the existing admin-gated endpoint (`get_current_admin` on api_service)
 * as an authorization probe for tools that talk to Postgres directly and so
 * have no endpoint of their own to enforce this — mcp_server never validates
 * JWTs itself.
 */
export async function assertAdminAuthorized(
  apiServiceUrl: string,
  authorization: string | undefined,
): Promise<void> {
  if (!authorization) {
    throw new Error("Missing Authorization header: an admin JWT is required.");
  }

  const response = await fetch(`${apiServiceUrl}/api/v1/admin/users/overview`, {
    method: "GET",
    headers: {
      Authorization: authorization,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Not authorized as admin (api_service returned ${response.status}).`);
  }
}
