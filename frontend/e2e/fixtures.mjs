export const ids = [
  "11111111-1111-4111-8111-111111111111",
  "22222222-2222-4222-8222-222222222222",
];
export const model = {
  id: "33333333-3333-4333-8333-333333333333",
  provider: "ollama",
  model: "qwen3-vl:2b",
};
export const bots = ids.map((id, i) => ({
  id,
  name: i
    ? "Asistente de indicadores institucionales y seguimiento del cumplimiento trimestral"
    : "Asistente operativo",
  description: "Interpreta tus indicadores con las fuentes asociadas.",
  behavior_instructions: "Responde en español y cita tus fuentes.",
  widget_settings: {
    primary_color: "#14a8ce",
    icon: "bot",
    welcome_message: "Hola, ¿qué indicador quieres analizar?",
  },
  configured_llm_model: model,
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-01T12:00:00Z",
}));
export const source = {
  id: "44444444-4444-4444-8444-444444444444",
  chatbot_id: ids[0],
  original_filename: "Informe de resultados y referencias compartidas.pdf",
  media_type: "application/pdf",
  size_bytes: 20480,
  status: "ready",
  error_code: null,
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-01T12:00:00Z",
  processed_at: "2026-10-01T12:00:00Z",
};
export const metrics = (id) => ({
  chatbot_id: id,
  started_at: null,
  ended_at: null,
  total_queries: id === ids[0] ? 12 : 8,
  completed_queries: id === ids[0] ? 10 : 6,
  failed_queries: 1,
  processing_queries: 1,
  measured_response_count: id === ids[0] ? 10 : 6,
  average_response_time_ms: 1200,
  interval: "day",
  status: null,
  series: [
    {
      period_start: "2026-10-01T00:00:00Z",
      total_queries: 4,
      completed_queries: 3,
      failed_queries: 1,
      processing_queries: 0,
      measured_response_count: 3,
      average_response_time_ms: 1200,
    },
    {
      period_start: "2026-10-02T00:00:00Z",
      total_queries: 0,
      completed_queries: 0,
      failed_queries: 0,
      processing_queries: 0,
      measured_response_count: 0,
      average_response_time_ms: null,
    },
    {
      period_start: "2026-10-03T00:00:00Z",
      total_queries: id === ids[0] ? 8 : 4,
      completed_queries: id === ids[0] ? 7 : 3,
      failed_queries: 0,
      processing_queries: 1,
      measured_response_count: id === ids[0] ? 7 : 3,
      average_response_time_ms: 1200,
    },
  ],
});
export async function prepare(
  page,
  { theme = "light", empty = false, authenticated = true } = {},
) {
  await page.addInitScript(
    ({ theme, authenticated }) => {
      if (window.top !== window) return;
      if (!sessionStorage.getItem("bidachat-qa-theme-initialized")) {
        localStorage.setItem("bidachat-theme", theme);
        sessionStorage.setItem("bidachat-qa-theme-initialized", "true");
      }
      if (authenticated)
        localStorage.setItem(
          "bidachat-session",
          JSON.stringify({
            accessToken: "isolated-qa-fixture",
            expiresAt: new Date(Date.now() + 3600000).toISOString(),
          }),
        );
    },
    { theme, authenticated },
  );
  const state = {
    bots: empty ? [] : structuredClone(bots),
    sources: new Map(ids.map((id) => [id, [{ ...source, chatbot_id: id }]])),
    queries: 0,
  };
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname.replace("/api/v1", ""),
      method = req.method();
    let body = {};
    if (path === "/auth/login")
      body = {
        access_token: "isolated-qa-fixture",
        token_type: "bearer",
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      };
    else if (path === "/auth/logout") return route.fulfill({ status: 204 });
    else if (path === "/llm-models")
      body = [
        model,
        {
          id: "77777777-7777-4777-8777-777777777777",
          provider: "openai",
          model: "gpt-5.6-luna",
        },
      ];
    else if (path === "/settings")
      body = {
        gemini_configured: false,
        openai_configured: false,
        openrouter_configured: false,
        embedding_provider: "ollama",
        embedding_model: "nomic-embed-text",
        embedding_dimensions: 768,
        document_max_size_bytes: 20971520,
        session_ttl_minutes: 120,
        widget_allowed_origins: ["http://127.0.0.1:4173"],
      };
    else if (path === "/documents") body = [source];
    else if (path === "/chatbots") {
      if (method === "POST") {
        const p = req.postDataJSON();
        const b = { ...bots[0], ...p, id: "55555555-5555-4555-8555-555555555555" };
        state.bots.push(b);
        body = b;
      } else body = state.bots;
    } else {
      const [, id, resource, docId] = path.split("/").slice(1);
      const b = state.bots.find((b) => b.id === id);
      if (resource === "metrics") body = metrics(id);
      else if (resource === "queries") {
        state.queries++;
        body = {
          answer:
            "El rendimiento operativo es 89,4 %. Revisa la fuente para el periodo consultado.",
          query_id: "66666666-6666-4666-8666-666666666666",
          status: "completed",
          response_time_ms: 1200,
        };
      } else if (resource === "documents") {
        if (method === "DELETE") {
          state.sources.set(
            id,
            (state.sources.get(id) ?? []).filter((d) => d.id !== docId),
          );
          return route.fulfill({ status: 204 });
        }
        if (method === "POST") {
          body = { ...source, chatbot_id: id };
          state.sources.set(id, [body]);
        } else body = state.sources.get(id) ?? [];
      } else if (method === "DELETE") {
        state.bots = state.bots.filter((b) => b.id !== id);
        return route.fulfill({ status: 204 });
      } else if (method === "PUT") {
        Object.assign(b, req.postDataJSON());
        b.configured_llm_model =
          [
            model,
            {
              id: "77777777-7777-4777-8777-777777777777",
              provider: "openai",
              model: "gpt-5.6-luna",
            },
          ].find((item) => item.id === b.configured_llm_model_id) ?? model;
        body = b;
      } else if (b) body = b;
      else return route.fulfill({ status: 404, json: { detail: "No encontrado" } });
    }
    return route.fulfill({ status: 200, json: body });
  });
  return state;
}
