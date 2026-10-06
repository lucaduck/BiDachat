import { chromium } from "@playwright/test";
import { prepare, ids } from "./fixtures.mjs";
import { writeFile } from "node:fs/promises";
const browser = await chromium.launch({ headless: true });
const results = [];
for (const theme of ["light", "dark"]) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await prepare(page, { theme });
  for (const [name, url] of [
    ["login", "/"],
    ...["Resumen", "Chatbots", "Documentos", "Métricas", "Configuración"].map((v) => [
      v,
      `/?view=${encodeURIComponent(v)}`,
    ]),
    ["editor", `/?view=Chatbots&edit=${ids[0]}`],
    ["preview", `/preview?chatbot_id=${ids[0]}`],
  ]) {
    if (name === "login")
      await page.addInitScript(() => localStorage.removeItem("bidachat-session"));
    else if (name === "Resumen")
      await page.addInitScript(() =>
        localStorage.setItem(
          "bidachat-session",
          JSON.stringify({
            accessToken: "isolated-qa-fixture",
            expiresAt: new Date(Date.now() + 3600000).toISOString(),
          }),
        ),
      );
    await page.goto(`http://127.0.0.1:3000${url}`);
    await page.waitForTimeout(650);
    if (name === "preview")
      await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
    await page.screenshot({
      path: `../docs/qa/frontend/before/${theme}-${name}.png`,
      fullPage: true,
    });
    results.push({
      theme,
      name,
      ...(await page.evaluate(() => ({
        resources: performance.getEntriesByType("resource").length,
        duration: performance.getEntriesByType("navigation")[0].duration,
        transferred: performance
          .getEntriesByType("resource")
          .reduce((n, r) => n + r.transferSize, 0),
      }))),
    });
  }
  await page.close();
}
await writeFile(
  "../docs/qa/frontend/before/measurements.json",
  JSON.stringify(
    {
      capturedAt: new Date().toISOString(),
      source: "Docker frontend before source refactor",
      results,
    },
    null,
    2,
  ),
);
await browser.close();
