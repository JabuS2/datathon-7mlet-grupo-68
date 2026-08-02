import { API_SERVICE_URL } from "@/lib/env";

export interface AuthUser {
  email: string;
  isAdmin: boolean;
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_SERVICE_URL}/api/v1/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    throw new Error("Invalid email or password");
  }

  const data = await res.json();
  return data.accessToken as string;
}

export async function me(token: string): Promise<AuthUser> {
  const res = await fetch(`${API_SERVICE_URL}/api/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    throw new Error("Session expired");
  }

  const data = await res.json();
  return { email: data.email, isAdmin: Boolean(data.isAdmin) };
}
