"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { ApiError } from "@/services/api-client";
import {
  login as loginRequest,
  logout as logoutRequest,
} from "@/services/auth-service";
import type { LoginRequest } from "@/types/api";
import {
  getSessionDelay,
  isSessionExpired,
  parseStoredSession,
  type StoredSession,
} from "@/services/session-utils";

const SESSION_STORAGE_KEY = "bidachat-session";

function removeStoredSession() {
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
  window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
}

type SessionContextValue = {
  token: string | null;
  isAuthenticated: boolean;
  isRestoring: boolean;
  sessionExpired: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  handleApiError: (error: unknown) => void;
};
const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [sessionExpired, setSessionExpired] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  const clearStoredSession = useCallback(() => {
    removeStoredSession();
    setToken(null);
    setExpiresAt(null);
  }, []);

  const storeSession = useCallback((session: StoredSession) => {
    window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setToken(session.accessToken);
    setExpiresAt(session.expiresAt);
  }, []);

  useEffect(() => {
    const restoreId = window.setTimeout(() => {
      const storedSession = parseStoredSession(
        window.localStorage.getItem(SESSION_STORAGE_KEY) ??
          window.sessionStorage.getItem(SESSION_STORAGE_KEY),
      );
      if (storedSession) storeSession(storedSession);
      else {
        if (window.localStorage.getItem(SESSION_STORAGE_KEY)) setSessionExpired(true);
        removeStoredSession();
      }
      setIsRestoring(false);
    }, 0);
    return () => window.clearTimeout(restoreId);
  }, [storeSession]);

  useEffect(() => {
    function syncSession(event: StorageEvent) {
      if (event.key !== SESSION_STORAGE_KEY) return;
      const session = parseStoredSession(event.newValue);
      setToken(session?.accessToken ?? null);
      setExpiresAt(session?.expiresAt ?? null);
    }
    window.addEventListener("storage", syncSession);
    return () => window.removeEventListener("storage", syncSession);
  }, []);

  useEffect(() => {
    if (!expiresAt) return;
    const timeout = window.setTimeout(() => {
      setSessionExpired(true);
      clearStoredSession();
    }, getSessionDelay(expiresAt));
    return () => window.clearTimeout(timeout);
  }, [clearStoredSession, expiresAt]);
  const logout = useCallback(async () => {
    const activeToken = token;
    clearStoredSession();
    if (!activeToken) return;
    try {
      await logoutRequest(activeToken);
    } catch {
      /* Removing the in-memory token remains safe. */
    }
  }, [clearStoredSession, token]);
  const value = useMemo(
    () => ({
      token,
      isAuthenticated: token !== null,
      isRestoring,
      sessionExpired,
      login: async (credentials: LoginRequest) => {
        const session = await loginRequest(credentials);
        if (isSessionExpired(session.expires_at)) throw new Error("Session expired");
        setSessionExpired(false);
        storeSession({
          accessToken: session.access_token,
          expiresAt: session.expires_at,
        });
      },
      logout,
      handleApiError: (error: unknown) => {
        if (error instanceof ApiError && error.status === 401) {
          setSessionExpired(true);
          clearStoredSession();
        }
      },
    }),
    [clearStoredSession, isRestoring, sessionExpired, logout, storeSession, token],
  );
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession must be used inside SessionProvider");
  return context;
}
