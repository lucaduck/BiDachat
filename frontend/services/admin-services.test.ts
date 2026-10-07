import { afterEach, describe, expect, it, vi } from "vitest";

import { createChatbot, deleteChatbot, updateChatbot } from "./chatbot-service";
import {
  listDocuments,
  removeDocumentAssociation,
  uploadDocument,
} from "./document-service";
import { getMetrics } from "./metrics-service";

const CHATBOT_ID = "11111111-1111-4111-8111-111111111111";
const PAYLOAD = {
  name: "Análisis",
  description: null,
  behavior_instructions: "Responder con claridad",
  configured_llm_model_id: "22222222-2222-4222-8222-222222222222",
};

describe("administrative API services", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("routes chatbot creation, update and deletion through the authorized API", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: CHATBOT_ID }), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: CHATBOT_ID }), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    await createChatbot("secret", PAYLOAD);
    await updateChatbot("secret", CHATBOT_ID, PAYLOAD);
    await deleteChatbot("secret", CHATBOT_ID);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "/api/v1/chatbots",
      `/api/v1/chatbots/${CHATBOT_ID}`,
      `/api/v1/chatbots/${CHATBOT_ID}`,
    ]);
    expect(fetchMock.mock.calls.map(([, options]) => options.method)).toEqual([
      "POST",
      "PUT",
      "DELETE",
    ]);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual(PAYLOAD);
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get("Authorization")).toBe(
      "Bearer secret",
    );
  });

  it("keeps document operations scoped to the selected chatbot and sends multipart data", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("[]", { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "doc" }), { status: 201 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["data"], "report.txt", { type: "text/plain" });
    await listDocuments("secret", CHATBOT_ID);
    await uploadDocument("secret", CHATBOT_ID, file);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `/api/v1/chatbots/${CHATBOT_ID}/documents`,
      `/api/v1/chatbots/${CHATBOT_ID}/documents`,
    ]);
    const uploadOptions = fetchMock.mock.calls[1][1] as RequestInit;
    expect(uploadOptions.body).toBeInstanceOf(FormData);
    expect((uploadOptions.body as FormData).get("file")).toEqual(file);
    expect(new Headers(uploadOptions.headers).has("Content-Type")).toBe(false);
  });

  it("removes only the selected chatbot document association", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    await removeDocumentAssociation("secret", CHATBOT_ID, "document-id");
    expect(fetchMock.mock.calls[0][0]).toBe(
      `/api/v1/chatbots/${CHATBOT_ID}/documents/document-id`,
    );
    expect(fetchMock.mock.calls[0][1].method).toBe("DELETE");
  });

  it("requests metrics for the selected chatbot and period", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ total_queries: 0 }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await getMetrics(
      "secret",
      CHATBOT_ID,
      "2026-09-01T00:00:00.000Z",
      "2026-09-23T00:00:00.000Z",
      { interval: "week", status: "failed", includeSeries: true },
    );
    const url = new URL(fetchMock.mock.calls[0][0], "https://example.test");
    expect(url.pathname).toBe(`/api/v1/chatbots/${CHATBOT_ID}/metrics`);
    expect(url.searchParams.get("started_at")).toBe("2026-09-01T00:00:00.000Z");
    expect(url.searchParams.get("ended_at")).toBe("2026-09-23T00:00:00.000Z");
    expect(url.searchParams.get("interval")).toBe("week");
    expect(url.searchParams.get("query_status")).toBe("failed");
    expect(url.searchParams.get("include_series")).toBe("true");
  });
});
