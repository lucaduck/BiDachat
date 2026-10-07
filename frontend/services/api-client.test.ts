import { afterEach, describe, expect, it, vi } from "vitest";

import { request } from "./api-client";

describe("request", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends a Bearer token and JSON body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await request("/chatbots", {
      method: "POST",
      token: "safe-token",
      body: JSON.stringify({ name: "Demo" }),
    });
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(options.headers);
    expect(headers.get("Authorization")).toBe("Bearer safe-token");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("returns undefined for a logout response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await expect(
      request<void>("/auth/logout", { method: "POST", token: "safe-token" }),
    ).resolves.toBeUndefined();
  });

  it("exposes only a safe error to callers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 401 })),
    );
    await expect(request("/chatbots", { token: "safe-token" })).rejects.toEqual(
      expect.objectContaining({
        status: 401,
        message: "No se pudo completar la operación. Inténtalo nuevamente.",
      }),
    );
  });
});
