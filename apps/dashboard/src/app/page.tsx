"use client";

import { Dashboard } from "@/components/Dashboard";
import { Login } from "@/components/Login";
import { Providers } from "@/components/Providers";
import { useAuth } from "@/hooks/useAuth";

export default function Home() {
  const { token, user, loading, signIn, signOut } = useAuth();

  if (loading) {
    return <div className="center-screen">Loading…</div>;
  }

  if (!token || !user || !user.isAdmin) {
    return <Login onSignIn={signIn} />;
  }

  return (
    <Providers token={token}>
      <Dashboard user={user} onSignOut={signOut} />
    </Providers>
  );
}
