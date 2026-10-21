import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const bot = "11111111-1111-4111-8111-111111111111";
const origin = "http://127.0.0.1:4173";
const source = readFileSync(
  resolve(process.cwd(), "../widget/src/bidachat-widget.js"),
  "utf8",
);

async function install(page: import("@playwright/test").Page, identity = false) {
  await page.route(`${origin}/widget.js`, (route) =>
    route.fulfill({
      contentType: "application/javascript; charset=utf-8",
      body: source,
    }),
  );
  await page.route(`${origin}/`, (route) =>
    route.fulfill({
      contentType: "text/html; charset=utf-8",
      body: `<html><body><script src="${origin}/widget.js" data-chatbot-id="${bot}" data-api-base="${origin}/api/v1" data-idle-minutes="1" ${identity ? 'data-identity-endpoint="/identity"' : ""}></script></body></html>`,
    }),
  );
}

test("new conversation and inactivity create separate memory", async ({ page }) => {
  await install(page);
  const requests: string[] = [];
  await page.route("**/queries", async (route) => {
    const data = route.request().postDataJSON();
    requests.push(data.conversation_id);
    await route.fulfill({
      json: { answer: "Respuesta", conversation_id: data.conversation_id },
    });
  });
  await page.goto(`${origin}/`);
  await page.locator("bidachat-widget .launcher").click();
  const ask = async () => {
    await page.locator("bidachat-widget .question").fill("Hola");
    await page.locator("bidachat-widget .send").click();
    await expect(page.locator("bidachat-widget .feedback")).toHaveCount(0);
  };
  await ask();
  await page.locator("bidachat-widget .new-conversation").click();
  await expect(page.locator("bidachat-widget .message-user")).toHaveCount(0);
  await ask();
  expect(requests[1]).not.toBe(requests[0]);
  await page.evaluate(
    ({ bot, origin }) => {
      sessionStorage.setItem(
        `bidachat-conversation:${origin}:${bot}:activity`,
        String(Date.now() - 120000),
      );
    },
    { bot, origin },
  );
  await page.reload();
  await page.locator("bidachat-widget .launcher").click();
  await ask();
  expect(requests[2]).not.toBe(requests[1]);
});

test("signed identity change clears the widget and suppresses an in-flight answer", async ({
  page,
}) => {
  await install(page, true);
  let subject = "a".repeat(64);
  let valid = true;
  await page.route(`${origin}/identity`, (route) =>
    valid
      ? route.fulfill({ json: { token: `v1.${subject}.1800000300.${"A".repeat(43)}` } })
      : route.fulfill({ status: 401 }),
  );
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let requested = false;
  await page.route("**/queries", async (route) => {
    requested = true;
    await pending;
    await route
      .fulfill({
        json: {
          answer: "Respuesta privada",
          conversation_id: route.request().postDataJSON().conversation_id,
        },
      })
      .catch(() => {});
  });
  await page.goto(`${origin}/`);
  await page.locator("bidachat-widget .launcher").click();
  await page.locator("bidachat-widget .question").fill("Dato privado");
  await page.locator("bidachat-widget .send").click();
  await expect.poll(() => requested).toBe(true);
  subject = "b".repeat(64);
  await page.evaluate(() =>
    window.dispatchEvent(new Event("bidachat:identity-changed")),
  );
  release();
  await expect(page.locator("bidachat-widget .launcher")).toBeVisible();
  await page.locator("bidachat-widget .launcher").click();
  await expect(page.locator("bidachat-widget .message-user")).toHaveCount(0);
  await expect(page.locator("bidachat-widget")).not.toContainText("Respuesta privada");
  valid = false;
  await page.locator("bidachat-widget .question").fill("Otra pregunta");
  await page.locator("bidachat-widget .send").click();
  await expect(page.locator("bidachat-widget .status")).toContainText(
    "verificar la sesión",
  );
});
