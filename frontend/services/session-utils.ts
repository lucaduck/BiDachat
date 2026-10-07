export type StoredSession = {
  accessToken: string;
  expiresAt: string;
};

export function isSessionExpired(expiresAt: string, now = Date.now()) {
  const expiration = Date.parse(expiresAt);
  return Number.isNaN(expiration) || expiration <= now;
}

export function getSessionDelay(expiresAt: string, now = Date.now()) {
  const expiration = Date.parse(expiresAt);
  return Number.isNaN(expiration) ? 0 : Math.max(0, expiration - now);
}

export function parseStoredSession(
  value: string | null,
  now = Date.now(),
): StoredSession | null {
  if (!value) return null;

  try {
    const stored = JSON.parse(value) as Partial<StoredSession>;
    if (
      typeof stored.accessToken !== "string" ||
      !stored.accessToken ||
      typeof stored.expiresAt !== "string" ||
      isSessionExpired(stored.expiresAt, now)
    ) {
      return null;
    }
    return { accessToken: stored.accessToken, expiresAt: stored.expiresAt };
  } catch {
    return null;
  }
}
