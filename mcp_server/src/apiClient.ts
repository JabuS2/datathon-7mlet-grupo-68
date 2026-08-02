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
