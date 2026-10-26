import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const chatbotId = "11111111-1111-4111-8111-111111111111";
const externalOrigin = "http://127.0.0.1:4173";
const source = readFileSync(
  resolve(process.cwd(), "../widget/src/bidachat-widget.js"),
  "utf8",
);

async function openWidget(page: Page, theme: "light" | "dark", preview = false) {
  await page.route(`${externalOrigin}/widget.js`, (route) =>
    route.fulfill({ contentType: "application/javascript", body: source }),
  );
  await page.route(`${externalOrigin}/`, (route) =>
    route.fulfill({
      contentType: "text/html",
      body: `<html><body><main>Dashboard externo</main><script src="${externalOrigin}/widget.js" data-chatbot-id="${chatbotId}" data-api-base="${externalOrigin}/api/v1" data-theme="${theme}" ${preview ? 'data-preview="true"' : ""}></script></body></html>`,
    }),
  );
  await page.route("**/queries", (route) => {
    const payload = route.request().postDataJSON();
    return route.fulfill({
      json: { answer: "Respuesta de prueba", conversation_id: payload.conversation_id },
    });
  });
  await page.goto(`${externalOrigin}/`);
  if (!preview) await page.locator("bidachat-widget .launcher").click();
}

for (const theme of ["light", "dark"] as const) {
  test(`survey can be omitted or submitted on an external page in ${theme} theme`, async ({
    page,
  }) => {
    const offers: unknown[] = [];
    const responses: unknown[] = [];
    await page.route("**/survey-offers", (route) => {
      offers.push(route.request().postDataJSON());
      return route.fulfill({ json: { state: "offered" } });
    });
    await page.route("**/survey-responses", (route) => {
      responses.push(route.request().postDataJSON());
      return route.fulfill({ json: { state: "submitted" } });
    });
    await openWidget(page, theme);
    const ask = async () => {
      await page.locator("bidachat-widget .question").fill("Hola");
      await page.locator("bidachat-widget .send").click();
      await expect(page.locator("bidachat-widget .message-assistant")).toHaveCount(2);
    };
    await expect(page.locator("bidachat-widget .finish-conversation")).toBeHidden();
    await ask();
    await page.locator("bidachat-widget .finish-conversation").click();
    await expect(page.locator("bidachat-widget .survey")).toBeVisible();
    await page.locator("bidachat-widget .close").click();
    await page.locator("bidachat-widget .launcher").click();
    await expect(page.locator("bidachat-widget .survey")).toBeVisible();
    await page.locator("bidachat-widget .omit-survey").click();
    await expect(page.locator("bidachat-widget .survey")).toBeHidden();
    expect(responses).toHaveLength(0);
    await ask();
    await page.locator("bidachat-widget .finish-conversation").click();
    await page.locator("bidachat-widget [name=satisfaction]").selectOption("5");
    await page.locator("bidachat-widget [name=comment]").fill("Muy útil");
    await page.locator("bidachat-widget .survey button[type=submit]").focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("bidachat-widget .survey")).toBeHidden();
    expect(offers).toHaveLength(2);
    expect(responses).toHaveLength(1);
    expect(responses[0]).toMatchObject({ satisfaction_score: 5, comment: "Muy útil" });
    expect((offers[0] as { conversation_id: string }).conversation_id).not.toBe(
      (offers[1] as { conversation_id: string }).conversation_id,
    );
  });
}

test("network failure keeps the survey draft and permits retry", async ({ page }) => {
  let attempts = 0;
  await page.route("**/survey-offers", (route) =>
    route.fulfill({ json: { state: "offered" } }),
  );
  await page.route("**/survey-responses", (route) => {
    attempts += 1;
    return attempts === 1
      ? route.fulfill({
          status: 503,
          json: { detail: "Servicio temporalmente no disponible" },
        })
      : route.fulfill({ json: { state: "submitted" } });
  });
  await openWidget(page, "light");
  await page.locator("bidachat-widget .question").fill("Hola");
  await page.locator("bidachat-widget .send").click();
  await expect(page.locator("bidachat-widget .finish-conversation")).toBeVisible();
  await page.locator("bidachat-widget .finish-conversation").click();
  await page.locator("bidachat-widget [name=satisfaction]").selectOption("4");
  await page.locator("bidachat-widget .survey button[type=submit]").click();
  await expect(page.locator("bidachat-widget .status")).toContainText("temporalmente");
  await expect(page.locator("bidachat-widget [name=satisfaction]")).toHaveValue("4");
  await page.locator("bidachat-widget .survey button[type=submit]").click();
  await expect(page.locator("bidachat-widget .survey")).toBeHidden();
  expect(attempts).toBe(2);
});

test("appearance preview never calls survey endpoints", async ({ page }) => {
  let surveyCalls = 0;
  await page.route("**/survey-*", (route) => {
    surveyCalls += 1;
    return route.fulfill({ status: 500 });
  });
  await openWidget(page, "dark", true);
  await expect(page.locator("bidachat-widget .finish-conversation")).toBeHidden();
  await expect(page.locator("bidachat-widget .question")).toBeDisabled();
  expect(surveyCalls).toBe(0);
});
