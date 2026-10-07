import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
// @ts-expect-error JavaScript fixture shared with the baseline capture.
import { prepare, ids, bots } from "./fixtures.mjs";
const edit = (id = ids[0], step = 0) => `/?view=Chatbots&edit=${id}&step=${step}`;
test.beforeEach(async ({ page }) => {
  await prepare(page);
});
test("external host sends only current selected visible page context", async ({
  page,
  baseURL,
}) => {
  const requests: Array<Record<string, string>> = [];
  const widgetSource = readFileSync(
    resolve(process.cwd(), "../widget/src/bidachat-widget.js"),
    "utf8",
  );
  await page.route("**/bidachat-widget.js", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: widgetSource,
    }),
  );
  await page.route(`**/api/v1/chatbots/${ids[0]}/queries`, async (route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({
        status: 204,
        headers: {
          "access-control-allow-origin": "http://127.0.0.1:4173",
          "access-control-allow-methods": "POST, OPTIONS",
          "access-control-allow-headers": "content-type",
        },
      });
      return;
    }
    requests.push(route.request().postDataJSON());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "access-control-allow-origin": "http://127.0.0.1:4173" },
      body: JSON.stringify({ answer: "Respuesta", response_time_ms: 10 }),
    });
  });
  await page.route("http://127.0.0.1:4173/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/html",
      body: `<!doctype html><html><body><main id="dashboard"><h1>Panel externo</h1><p id="metric">Ventas 42</p><p hidden>Dato oculto</p><p data-bidachat-ignore>Dato excluido</p><form><label>Clave privada<input value="secreto"></label></form><button>Acción privada</button></main><script src="${baseURL}/bidachat-widget.js" data-chatbot-id="${ids[0]}" data-context-selector="#dashboard"></script></body></html>`,
    }),
  );
  await page.goto("http://127.0.0.1:4173/");
  await page.locator("bidachat-widget .launcher").click();
  await page.locator("bidachat-widget .question").fill("¿Cuánto?");
  await page.locator("bidachat-widget .send").click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0].page_context).toContain("Ventas 42");
  expect(requests[0].page_context).not.toMatch(/oculto|excluido|privada|secreto/i);
  await page.locator("#metric").evaluate((element) => {
    element.textContent = "Ventas 57";
  });
  await page.locator("bidachat-widget .question").fill("¿Y ahora?");
  await page.locator("bidachat-widget .send").click();
  await expect.poll(() => requests.length).toBe(2);
  expect(requests[1].page_context).toContain("Ventas 57");
  expect(requests[1].page_context).not.toContain("Ventas 42");
  await page.locator("#metric").evaluate((element) => {
    element.textContent = "Valor " + "7".repeat(7000);
  });
  await page.locator("bidachat-widget .question").fill("¿Límite?");
  await page.locator("bidachat-widget .send").click();
  await expect.poll(() => requests.length).toBe(3);
  expect(requests[2].page_context.length).toBe(6000);
  await page.locator("bidachat-widget").evaluate(() => {
    document.querySelector<HTMLScriptElement>(
      "script[data-context-selector]",
    )!.dataset.contextSelector = "##invalid";
  });
  await page.locator("bidachat-widget .question").fill("¿Sin región?");
  await page.locator("bidachat-widget .send").click();
  await expect.poll(() => requests.length).toBe(4);
  expect(requests[3].page_context).toBeUndefined();
});
test("navigation, history, deep link, refresh, editor close and preview return", async ({
  page,
  context,
}) => {
  await page.goto("/?view=Chatbots");
  await page.getByRole("link", { name: "Editar", exact: true }).first().click();
  await expect(page).toHaveURL(new RegExp(ids[0]));
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await expect(page).toHaveURL(/step=1/);
  await page.goBack();
  await expect(page.getByLabel("Nombre del chatbot")).toBeVisible();
  await page.goForward();
  await expect(page.locator("#widget-color")).toBeVisible();
  await page.reload();
  await expect(page.locator("#widget-color")).toBeVisible();
  await page.goto(edit(ids[1]));
  await expect(page.getByLabel("Nombre del chatbot")).toHaveValue(bots[1].name);
  await page.goBack();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(bots[0].name);
  await expect(page.locator("#widget-color")).toBeVisible();
  await page.goForward();
  await expect(page.getByLabel("Nombre del chatbot")).toHaveValue(bots[1].name);
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page).toHaveURL(/\?view=Chatbots$/);
  await page.reload();
  await expect(page.getByRole("link", { name: "Editar", exact: true })).toHaveCount(2);
  await page.goto(edit(ids[0], 4));
  await page.getByRole("link", { name: "Abrir vista previa" }).click();
  await page.getByRole("link", { name: "Volver al editor" }).click();
  await expect(page).toHaveURL(/step=4/);
  await expect(page.getByRole("button", { name: "Finalizar" })).toBeVisible();
  const tab = await context.newPage();
  await prepare(tab);
  await tab.goto(edit(ids[1], 3));
  await expect(tab.getByRole("heading", { level: 1 })).toHaveText(bots[1].name);
  await tab.close();
});
test("draft is preserved after cancelling exit, then discarded on confirmed exit", async ({
  page,
}) => {
  await page.goto(edit());
  await page.getByLabel("Nombre del chatbot").fill("Borrador");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("link", { name: "Documentos", exact: true }).click();
  await expect(page.getByLabel("Nombre del chatbot")).toHaveValue("Borrador");
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.goBack();
  await expect(page.getByLabel("Nombre del chatbot")).toHaveValue("Borrador");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("link", { name: "Documentos", exact: true }).click();
  await expect(page.getByLabel("Archivo", { exact: true })).toBeAttached();
});
test("invalid and deleted routes recover without opening creation, 404 recovers", async ({
  page,
}) => {
  await page.goto("/?view=Incorrecta");
  await expect(
    page.getByText("La dirección contiene parámetros", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Volver a una vista válida" }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto(edit("99999999-9999-4999-8999-999999999999"));
  await expect(
    page.getByRole("heading", { name: "Este chatbot no está disponible" }),
  ).toBeVisible();
  await expect(page.getByLabel("Nombre del chatbot")).toHaveCount(0);
  await page.getByRole("button", { name: "Volver a Chatbots" }).click();
  await page.goto("/does-not-exist");
  await expect(
    page.getByRole("heading", { name: /No encontramos esta página/i }),
  ).toBeVisible();
  await page.getByRole("link").first().click();
  await expect(page).toHaveURL(/\/$/);
});
test("create, personalize, save and reopen", async ({ page }) => {
  await page.goto("/?view=Chatbots");
  await page.getByRole("button", { name: "Crear chatbot", exact: true }).click();
  await page.getByLabel("Nombre del chatbot").fill("Asistente QA");
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.locator("#widget-color").fill("#225577");
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.getByLabel("Mensaje de bienvenida").fill("Hola desde QA");
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await expect(
    page.getByRole("heading", { name: "Base de conocimiento" }),
  ).toBeVisible();
  await expect(page).toHaveURL(/edit=55555555/);
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await expect(page.getByLabel("Script de integración")).toHaveValue(/Hola desde QA/);
  await page.getByRole("button", { name: "Finalizar" }).click();
  await expect(page.getByRole("heading", { name: "Asistente QA" })).toBeVisible();
});
test("provider filters models and changing it requires a new model", async ({
  page,
}) => {
  await page.goto(edit(ids[0], 2));
  await expect(page.getByLabel("Proveedor de IA")).toHaveValue("ollama");
  await expect(page.getByLabel("Modelo de lenguaje")).toHaveValue(
    bots[0].configured_llm_model.id,
  );
  await expect(page.locator("#wizard-model option")).toHaveCount(2);
  await page.getByLabel("Proveedor de IA").selectOption("openai");
  await expect(page.getByLabel("Modelo de lenguaje")).toHaveValue("");
  await expect(page.locator("#wizard-model option")).toHaveCount(2);
  await expect(page.locator("#wizard-model option").last()).toHaveText("gpt-5.6-luna");
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await expect(page).toHaveURL(/step=2/);
  await page
    .getByLabel("Modelo de lenguaje")
    .selectOption("77777777-7777-4777-8777-777777777777");
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await expect(page).toHaveURL(/step=3/);
  await page.goto(edit(ids[0], 2));
  await expect(page.getByLabel("Proveedor de IA")).toHaveValue("openai");
  await expect(page.getByLabel("Modelo de lenguaje")).toHaveValue(
    "77777777-7777-4777-8777-777777777777",
  );
});
test("shared source can be removed and associated without changing the other bot", async ({
  page,
}) => {
  await page.goto(edit(ids[0], 3));
  await page.getByRole("button", { name: "Quitar del contexto" }).click();
  await expect(page.getByRole("checkbox")).toHaveCount(1);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Asociar seleccionados" }).click();
  await expect(page.getByRole("button", { name: "Quitar del contexto" })).toHaveCount(
    1,
  );
  await page.goto(edit(ids[1], 3));
  await expect(page.getByRole("button", { name: "Quitar del contexto" })).toHaveCount(
    1,
  );
});
test("documents and metrics filters keep their URL and avoid stale data", async ({
  page,
}) => {
  await page.goto("/?view=Documentos");
  await page.getByLabel("Chatbot", { exact: true }).selectOption(ids[1]);
  await expect(page).toHaveURL(new RegExp(`chatbot_id=${ids[1]}`));
  await page.reload();
  await expect(page.getByLabel("Chatbot", { exact: true })).toHaveValue(ids[1]);
  await page.goto("/?view=M%C3%A9tricas");
  await page.getByLabel("Periodo").selectOption("7");
  await page.getByLabel("Chatbot", { exact: true }).selectOption(ids[1]);
  await page.reload();
  await expect(page.getByLabel("Periodo")).toHaveValue("7");
  await expect(page.getByLabel("Chatbot", { exact: true })).toHaveValue(ids[1]);
  await expect(page.locator(".metric-card").first().locator("dd")).toHaveText("8");
});
test("clipboard denial has manual copy fallback", async ({ page }) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: () => Promise.reject(new Error("Denied")) },
    }),
  );
  await page.goto("/?view=Configuraci%C3%B3n");
  await page.getByRole("button", { name: "Copiar código" }).click();
  await expect(page.locator(".alert-error")).toContainText("manualmente");
  await expect(page.getByLabel("Código de integración")).toHaveValue(/data-chatbot-id/);
});
test("expired session returns to the same editor after login", async ({ page }) => {
  await page.addInitScript(() => {
    if (window.top !== window) return;
    localStorage.setItem(
      "bidachat-session",
      JSON.stringify({
        accessToken: "expired-qa-fixture",
        expiresAt: new Date(Date.now() - 60000).toISOString(),
      }),
    );
  });
  await page.goto(edit(ids[1], 2));
  await expect(page.getByText("Tu sesión terminó.", { exact: false })).toBeVisible();
  await page.getByLabel("Correo institucional").fill("qa@example.test");
  await page.getByLabel("Contraseña", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await expect(page.getByLabel("Mensaje de bienvenida")).toBeVisible();
  await expect(page).toHaveURL(new RegExp(ids[1]));
});

test("long conversation scrolls inside the widget and appearance preview makes no queries", async ({
  page,
}) => {
  let queries = 0;
  let querySockets = 0;
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.endsWith("/queries")) queries++;
  });
  page.on("websocket", (socket) => {
    if (socket.url().endsWith("/queries/ws")) querySockets++;
  });
  await page.goto(edit(ids[0], 1));
  await page.locator("#widget-color").fill("#225577");
  const frame = page.frameLocator("iframe[title='Vista visual del chatbot']");
  await expect(frame.locator("bidachat-widget")).toBeVisible();
  await expect(frame.getByRole("textbox", { name: "Pregunta" })).toBeDisabled();
  expect(queries).toBe(0);
  await page.setViewportSize({ width: 320, height: 700 });
  await page.goto(`/preview?chatbot_id=${ids[0]}`);
  await page.route("**/queries", (route) =>
    route.fulfill({
      json: {
        answer: "La fuente explica el indicador y su periodo. ".repeat(50),
        status: "completed",
        query_id: "66666666-6666-4666-8666-666666666666",
        response_time_ms: 1200,
      },
    }),
  );
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  for (let i = 0; i < 4; i++) {
    await page.getByRole("textbox", { name: "Pregunta" }).fill(`Consulta ${i}`);
    await page.getByRole("button", { name: "Enviar consulta" }).click();
    await expect(page.locator("bidachat-widget .message-assistant")).toHaveCount(i + 2);
  }
  expect(queries).toBe(4);
  expect(querySockets).toBe(0);
  const log = page.getByRole("log", { name: "Conversación" });
  expect(
    await log.evaluate((el) => el.scrollHeight > el.clientHeight && el.scrollTop > 0),
  ).toBeTruthy();
  await log.focus();
  await log.press("Home");
  await expect(log).toBeFocused();
  await expect(page.getByRole("button", { name: "Enviar consulta" })).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
});

test("assistant answers render readable lists without exposing markup", async ({
  page,
}) => {
  await page.route("**/queries", (route) =>
    route.fulfill({
      json: {
        answer:
          "Estos documentos están disponibles:\n\n1. **Marco teórico**\n2. **SciTE**\n\nConsulta <script>alert('x')</script> para más detalles.",
        status: "completed",
        query_id: "66666666-6666-4666-8666-666666666666",
        response_time_ms: 1200,
      },
    }),
  );
  await page.goto(`/preview?chatbot_id=${ids[0]}`);
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  await page.getByRole("textbox", { name: "Pregunta" }).fill("¿Qué documentos tienes?");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  const answer = page.locator("bidachat-widget .message-assistant").last();
  await expect(answer.locator("ol li")).toHaveCount(2);
  await expect(answer.locator("strong").first()).toHaveText("Marco teórico");
  await expect(answer).not.toContainText("**");
  await expect(answer.locator("script")).toHaveCount(0);
  await expect(answer).toContainText("<script>alert('x')</script>");
});

test("administrative API failures show errors and recover on reload", async ({
  page,
}) => {
  for (const [view, endpoint] of [
    ["Resumen", "**/metrics*"],
    ["Chatbots", "**/llm-models"],
    ["Documentos", `**/chatbots/${ids[0]}/documents`],
    ["Métricas", "**/metrics*"],
    ["Configuración", "**/settings"],
  ]) {
    await page.route(endpoint, (route) =>
      route.fulfill({ status: 503, json: { detail: "Unavailable" } }),
    );
    await page.goto(`/?view=${encodeURIComponent(view)}`);
    await expect(page.locator(".alert-error")).toBeVisible();
    await page.unroute(endpoint);
    await page.reload();
    await expect(page.locator(".alert-error")).toHaveCount(0);
    await expect(page.locator(".loading-state")).toHaveCount(0);
  }
});
test("widget text, paste, remove, capture denied and retry keep user input", async ({
  page,
}) => {
  await page.goto(`/preview?chatbot_id=${ids[0]}`);
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  const question = page.getByRole("textbox", { name: "Pregunta" });
  await question.fill("Interpreta el rendimiento");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await expect(page.locator("bidachat-widget .message-assistant").last()).toContainText(
    "89,4",
  );
  await question.evaluate((el) => {
    const dt = new DataTransfer();
    dt.items.add(
      new File([new Uint8Array([137, 80, 78, 71])], "pegada.png", {
        type: "image/png",
      }),
    );
    el.dispatchEvent(
      new ClipboardEvent("paste", {
        clipboardData: dt,
        bubbles: true,
        cancelable: true,
      }),
    );
  });
  await expect(
    page.getByRole("button", { name: "Quitar imagen adjunta" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Quitar imagen adjunta" }).click();
  await expect(
    page.getByRole("button", { name: "Quitar imagen adjunta" }),
  ).toBeHidden();
  await page.evaluate(() =>
    Object.defineProperty(navigator, "mediaDevices", {
      value: {
        getDisplayMedia: () =>
          Promise.reject(new DOMException("Cancelled", "NotAllowedError")),
      },
      configurable: true,
    }),
  );
  await page.getByRole("button", { name: "Capturar pantalla" }).click();
  await expect(question).toBeEnabled();
  await page.route("**/queries", (r) =>
    r.fulfill({
      status: 503,
      json: { detail: "Proveedor temporalmente no disponible" },
    }),
  );
  await question.fill("Reintentar pregunta");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await expect(question).toHaveValue("Reintentar pregunta");
  await expect(page.locator("bidachat-widget .feedback-error")).toBeVisible();
  await question.press("Escape");
  await expect(
    page.getByRole("button", { name: "Abrir asistente BIDACHAT" }),
  ).toBeFocused();
});
test("mobile menu traps focus, Escape returns focus and collapse persists", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Menú", exact: true }).click();
  await expect(page.getByRole("link", { name: "Resumen", exact: true })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Menú", exact: true })).toBeFocused();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "Contraer menú lateral" }).click();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Expandir menú lateral" }),
  ).toBeVisible();
});

test("current wizard step stays visible on narrow screens without moving page scroll", async ({
  page,
}) => {
  for (const width of [320, 390, 768, 1089]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const step of [3, 4]) {
      await page.goto(edit(ids[0], step));
      const current = page.locator('.wizard-steps [aria-current="step"]');
      await expect(current).toBeVisible();
      await expect
        .poll(async () =>
          current.evaluate((el) => {
            const item = el.getBoundingClientRect(),
              list = el.parentElement!.getBoundingClientRect();
            return item.left >= list.left - 1 && item.right <= list.right + 1;
          }),
        )
        .toBeTruthy();
      expect(
        await current.evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
      ).toBeGreaterThanOrEqual(12);
      expect(await page.evaluate(() => scrollY)).toBe(0);
    }
  }
});

test("mobile integration target exposes the complete selected chatbot name", async ({
  page,
}) => {
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/?view=Configuraci%C3%B3n");
    await page.getByLabel("Chatbot para integrar").selectOption(ids[1]);
    await expect(page.locator(".settings-selected-chatbot strong")).toHaveText(
      bots[1].name,
    );
    const select = await page.getByLabel("Chatbot para integrar").boundingBox();
    expect(select!.width).toBeGreaterThan(width * 0.65);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  }
});
for (const theme of ["light", "dark"])
  test(`${theme}: all surfaces and sizes, overflow, accessible controls and assets`, async ({
    page,
  }) => {
    await page.addInitScript(
      (theme) => localStorage.setItem("bidachat-theme", theme),
      theme,
    );
    const violations: unknown[] = [];
    for (const width of [1440, 1089, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const [name, path] of [
        ["summary", "/"],
        ["chatbots", "/?view=Chatbots"],
        ["documents", "/?view=Documentos"],
        ["metrics", "/?view=M%C3%A9tricas"],
        ["settings", "/?view=Configuraci%C3%B3n"],
        ["editor", edit(ids[0], 1)],
        ["knowledge", edit(ids[0], 3)],
        ["preview", `/preview?chatbot_id=${ids[0]}`],
      ]) {
        await page.goto(path);
        await expect(page.locator(".loading-state")).toHaveCount(0);
        if (name === "preview")
          await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
        await page.screenshot({
          path: `../docs/qa/frontend/after/${theme}-${width}-${name}.png`,
          fullPage: true,
        });
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth + 1,
          ),
          `${name} overflow at ${width}`,
        ).toBeTruthy();
        if (width === 1440 || width === 390) {
          const a = await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
          if (a.violations.length)
            violations.push({ theme, width, name, violations: a.violations });
        }
      }
    }
    expect(violations).toEqual([]);
  });

test("empty states, zero measurements, request failure and retry", async ({ page }) => {
  await page.route("**/chatbots", (r) => r.fulfill({ json: [] }));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Aún no hay chatbots" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Documentos", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No hay chatbots" })).toBeVisible();
  await page.unroute("**/chatbots");
  let fails = true;
  await page.route("**/metrics*", (r) =>
    fails
      ? r.fulfill({ status: 503, json: { detail: "Unavailable" } })
      : r.fulfill({
          json: {
            chatbot_id: ids[0],
            total_queries: 0,
            completed_queries: 0,
            failed_queries: 0,
            processing_queries: 0,
            measured_response_count: 0,
            average_response_time_ms: null,
            started_at: null,
            ended_at: null,
          },
        }),
  );
  await page.goto("/?view=M%C3%A9tricas");
  await expect(page.locator(".alert-error")).toContainText("No se pudieron cargar");
  fails = false;
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.getByText("No disponible", { exact: true })).toBeVisible();
  await expect(
    page.getByText("No hay consultas para los filtros aplicados.", { exact: true }),
  ).toBeVisible();
});
test("failed save preserves inputs and deletion requires confirmation", async ({
  page,
}) => {
  await page.goto(edit());
  await page.getByLabel("Nombre del chatbot").fill("Nombre que debe conservarse");
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.route(`**/chatbots/${ids[0]}`, (r) =>
    r.fulfill({ status: 503, json: { detail: "Unavailable" } }),
  );
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await expect(page.locator(".alert-error")).toContainText("No se pudo guardar");
  await page.getByRole("button", { name: "Anterior" }).click();
  await page.getByRole("button", { name: "Anterior" }).click();
  await expect(page.getByLabel("Nombre del chatbot")).toHaveValue(
    "Nombre que debe conservarse",
  );
  page.once("dialog", (d) => d.accept());
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.unroute(`**/chatbots/${ids[0]}`);
  await page.getByRole("button", { name: "Eliminar", exact: true }).first().click();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page.getByRole("link", { name: "Editar", exact: true })).toHaveCount(2);
  await page.getByRole("button", { name: "Eliminar", exact: true }).first().click();
  await page.getByRole("button", { name: "Confirmar eliminación" }).click();
  await expect(page.getByRole("link", { name: "Editar", exact: true })).toHaveCount(1);
});
test("keyboard skip, reduced motion, login validation and 200 percent layout", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Resumen operativo");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Ir al contenido" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#workspace-content")).toBeFocused();
  await page.setViewportSize({ width: 720, height: 500 });
  await page.goto(edit(ids[0], 3));
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  await expect(page.getByRole("button", { name: "Menú", exact: true })).toBeVisible();
  await page.addInitScript(() => localStorage.removeItem("bidachat-session"));
  await page.goto("/");
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await expect(page.getByLabel("Correo institucional")).toBeFocused();
  await page.getByLabel("Correo institucional").fill("qa@example.test");
  await page.getByLabel("Contraseña", { exact: true }).fill("secret");
  await page.getByRole("button", { name: "Mostrar contraseña" }).click();
  await expect(page.getByLabel("Contraseña", { exact: true })).toHaveAttribute(
    "type",
    "text",
  );
  const a = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(a.violations).toEqual([]);
});
