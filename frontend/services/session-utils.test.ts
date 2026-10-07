import { describe, expect, it } from "vitest";

import { getSessionDelay, isSessionExpired, parseStoredSession } from "./session-utils";

describe("session expiration", () => {
  it("rejects expired and malformed timestamps", () => {
    expect(
      isSessionExpired("2026-01-01T00:00:00Z", Date.parse("2026-01-02T00:00:00Z")),
    ).toBe(true);
    expect(isSessionExpired("invalid-date")).toBe(true);
  });

  it("calculates the remaining time for valid sessions", () => {
    expect(
      getSessionDelay("2026-01-02T00:00:00Z", Date.parse("2026-01-01T00:00:00Z")),
    ).toBe(86_400_000);
  });

  it("restores only a valid stored session", () => {
    const now = Date.parse("2026-01-01T00:00:00Z");
    expect(
      parseStoredSession(
        JSON.stringify({
          accessToken: "session-token",
          expiresAt: "2026-01-01T00:01:00Z",
        }),
        now,
      ),
    ).toEqual({ accessToken: "session-token", expiresAt: "2026-01-01T00:01:00Z" });
    expect(parseStoredSession("invalid", now)).toBeNull();
    expect(
      parseStoredSession(
        JSON.stringify({
          accessToken: "expired-token",
          expiresAt: "2025-12-31T23:59:00Z",
        }),
        now,
      ),
    ).toBeNull();
  });
});
