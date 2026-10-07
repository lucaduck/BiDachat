"use client";

import { AdminWorkspace } from "@/components/admin/admin-workspace";
import { LoginScreen } from "@/components/auth/login-screen";
import { SessionProvider, useSession } from "@/components/auth/session-provider";
import { LoadingState } from "@/components/ui/status";

function Application() {
  const { isAuthenticated, isRestoring } = useSession();
  if (isRestoring) {
    return (
      <main className="session-restoring">
        <LoadingState label="Restaurando sesión…" />
      </main>
    );
  }
  return isAuthenticated ? <AdminWorkspace /> : <LoginScreen />;
}

export default function HomePage() {
  return (
    <SessionProvider>
      <Application />
    </SessionProvider>
  );
}
