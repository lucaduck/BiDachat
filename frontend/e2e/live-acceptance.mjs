import { chromium } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
const credentials = JSON.parse(
  await readFile(
    process.env.BIDACHAT_QA_CREDENTIALS ?? "/tmp/bidachat-ui-qa/credentials.json",
    "utf8",
  ),
);
const prefix = "QA interfaz " + credentials.userId.slice(0, 8);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const api = "http://127.0.0.1:3000/api/v1";
let auth;
const results = [];
let server, deniedServer;
const record = (caseId, value) => {
  results.push({ caseId, ...value });
  console.log(caseId + ": passed");
};
try {
  await page.goto("http://127.0.0.1:3000/?view=Chatbots&mode=create");
  await page.getByLabel("Correo institucional").fill(credentials.email);
  await page.getByLabel("Contraseña", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await page.getByLabel("Nombre del chatbot").fill(prefix);
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.locator("#widget-color").fill("#225577");
  await page.getByLabel("Análisis", { exact: true }).check();
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  const modelsResponse = await page.request.get(`${api}/llm-models`, {
    headers: {
      Authorization: `Bearer ${await page.evaluate(() => JSON.parse(localStorage.getItem("bidachat-session")).accessToken)}`,
    },
  });
  const selectedModel = (await modelsResponse.json()).find(
    (model) => model.id === credentials.modelId,
  );
  if (!selectedModel) throw new Error("Configured QA model is unavailable");
  await page.getByLabel("Proveedor de IA").selectOption(selectedModel.provider);
  await page.getByLabel("Modelo de lenguaje").selectOption(credentials.modelId);
  await page
    .getByLabel("Instrucciones de comportamiento")
    .fill("Responde brevemente en español, usa la información documental.");
  await page
    .getByLabel("Mensaje de bienvenida")
    .fill("Hola, revisemos el indicador Faro.");
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await page.getByRole("heading", { name: "Base de conocimiento" }).waitFor();
  const id = new URL(page.url()).searchParams.get("edit");
  credentials.botIds.push(id);
  await writeFile(
    process.env.BIDACHAT_QA_CREDENTIALS ?? "/tmp/bidachat-ui-qa/credentials.json",
    JSON.stringify(credentials),
  );
  auth = await page.evaluate(
    () => JSON.parse(localStorage.getItem("bidachat-session")).accessToken,
  );
  record("live-create", { botId: id });
  await page.locator("#wizard-document").setInputFiles({
    name: "qa-faro.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "El indicador Faro tiene un valor de 137 unidades en septiembre de 2026. La meta institucional es 150 unidades.",
    ),
  });
  await page.getByRole("button", { name: "Cargar fuente" }).click();
  await page
    .getByText("Documento procesado correctamente.", { exact: true })
    .waitFor({ timeout: 600000 });
  record("live-local-embedding", { status: "ready" });
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  const snippet = await page.getByLabel("Script de integración").inputValue();
  if (!snippet.includes("#225577") || !snippet.includes('data-icon="chart"'))
    throw new Error("Saved appearance mismatch");
  await page.getByRole("link", { name: "Abrir vista previa" }).click();
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  await page
    .getByRole("textbox", { name: "Pregunta" })
    .fill("¿Cuál es el valor del indicador Faro en septiembre?");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await page
    .locator("bidachat-widget .message-assistant")
    .last()
    .filter({ hasText: "137" })
    .waitFor({ timeout: 600000 });
  record("live-rag-query", { containsExpectedValue: true });
  await page.getByRole("link", { name: "Volver al editor" }).click();
  await page.getByRole("button", { name: "Finalizar" }).waitFor();
  record("live-preview-return", { step: 4 });
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Dashboard externo de QA</title></head><body style="font-family:system-ui;background:#f4f7fb;padding:32px"><h1>Dashboard independiente</h1><p>Datos sintéticos de prueba: Faro 137 unidades.</p><section id="qa-chart" style="padding:24px;background:white;width:480px"><h2>Comparación trimestral</h2><div style="background:#147cba;width:150px;height:40px;margin:12px;color:white">Periodo A: 40</div><div style="background:#b22a42;width:300px;height:40px;margin:12px;color:white">Periodo B: 80</div></section>${snippet}</body></html>`;
  server = createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  });
  await new Promise((r) => server.listen(4173, "0.0.0.0", r));
  deniedServer = createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  });
  await new Promise((r) => deniedServer.listen(4174, "0.0.0.0", r));
  await page.goto("http://127.0.0.1:4173");
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  await page
    .getByRole("textbox", { name: "Pregunta" })
    .fill("¿Cuántas unidades tiene Faro?");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await page
    .locator("bidachat-widget .message-assistant")
    .last()
    .filter({ hasText: "137" })
    .waitFor({ timeout: 600000 });
  record("live-external-origin-allowed", {
    origin: "http://127.0.0.1:4173",
    imports: "generated script only",
  });
  const image = await page.locator("#qa-chart").screenshot();
  await page
    .getByLabel("Seleccionar imagen")
    .setInputFiles({ name: "qa-chart.png", mimeType: "image/png", buffer: image });
  await page
    .getByRole("textbox", { name: "Pregunta" })
    .fill("Describe y compara los dos periodos de la imagen adjunta.");
  const before = await page.locator("bidachat-widget .message-assistant").count();
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await page.waitForFunction(
    (n) =>
      document
        .querySelector("bidachat-widget")
        .shadowRoot.querySelectorAll(".message-assistant").length > n,
    before,
    { timeout: 600000 },
  );
  record("live-multimodal-query", {
    imageType: "image/png",
    source: "synthetic external dashboard",
    responseReceived: true,
  });
  await page.goto("http://127.0.0.1:4174");
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  await page.getByRole("textbox", { name: "Pregunta" }).fill("Origen no autorizado");
  await page.getByRole("button", { name: "Enviar consulta" }).click();
  await page.locator("bidachat-widget .feedback-error").waitFor();
  record("live-external-origin-denied", { origin: "http://127.0.0.1:4174" });
  const metrics = await fetch(`${api}/chatbots/${id}/metrics`, {
    headers: { Authorization: `Bearer ${auth}` },
  }).then((r) => r.json());
  if (metrics.completed_queries < 2 || !metrics.measured_response_count)
    throw new Error("Metrics missing");
  record("live-metrics", {
    completed: metrics.completed_queries,
    measured: metrics.measured_response_count,
  });
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
  results.push({ error: error.message });
} finally {
  server?.close();
  deniedServer?.close();
  await writeFile(
    new URL("../../docs/qa/frontend/live-results.json", import.meta.url),
    JSON.stringify({ capturedAt: new Date().toISOString(), results }, null, 2),
  );
  await browser.close();
}
