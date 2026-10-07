import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
// @ts-expect-error JavaScript fixture shared with the workspace acceptance tests.
import { prepare, ids } from "./fixtures.mjs";

// RF-28 / CA-UC03-06: choices reach the preview, persistence and embed code.
test("appearance proposals update the widget and survive saving", async ({ page }) => {
  const state = await prepare(page);
  await page.goto(`/?view=Chatbots&edit=${ids[0]}&step=1`);
  const preview = page.frameLocator("iframe[title='Vista visual del chatbot']");
  const host = preview.locator("bidachat-widget");
  for (const [label, color] of [
    ["Turquesa BIDACHAT", "#14a8ce"],
    ["Azul", "#2563eb"],
    ["Índigo", "#4f46e5"],
    ["Violeta", "#7c3aed"],
    ["Esmeralda", "#059669"],
    ["Coral", "#e45756"],
    ["Ámbar", "#d97706"],
    ["Grafito", "#334155"],
  ]) {
    await page.getByRole("radio", { name: label, exact: true }).check();
    await expect(page.locator("#widget-color")).toHaveValue(color);
    await expect(host).toHaveAttribute("style", new RegExp(color));
  }
  const symbols = new Set<string>();
  for (const label of [
    "Robot",
    "Conversación",
    "Análisis",
    "Conocimiento",
    "Asistente IA",
    "Soporte",
  ]) {
    await page.getByRole("radio", { name: label, exact: true }).check();
    await expect(page.getByRole("radio", { name: label, exact: true })).toBeChecked();
    // Wait for the debounced iframe to render this selection.
    await expect
      .poll(async () => {
        const symbol = await preview.locator(".avatar svg").innerHTML();
        return symbols.has(symbol) ? "old" : symbol;
      })
      .not.toBe("old");
    const symbol = await preview.locator(".avatar svg").innerHTML();
    expect(symbol).not.toContain("undefined");
    symbols.add(symbol);
  }
  expect(symbols.size).toBe(6);
  await page.locator("#widget-color").fill("#104957");
  await expect(
    page.getByRole("group", { name: "Colores sugeridos" }).locator("input:checked"),
  ).toHaveCount(0);
  await expect(host).toHaveAttribute("style", /#104957/);
  await page.getByRole("button", { name: "Siguiente paso" }).click();
  await page.getByRole("button", { name: "Guardar y continuar" }).click();
  await expect(
    page.getByRole("heading", { name: "Base de conocimiento" }),
  ).toBeVisible();
  expect(state.bots[0].widget_settings).toMatchObject({
    primary_color: "#104957",
    icon: "headset",
  });
  await page.goto(`/?view=Chatbots&edit=${ids[0]}&step=1`);
  await expect(page.getByRole("radio", { name: "Soporte", exact: true })).toBeChecked();
  await expect(page.locator("#widget-color")).toHaveValue("#104957");
  await page.goto(`/?view=Chatbots&edit=${ids[0]}&step=4`);
  await expect(page.getByLabel("Script de integración")).toHaveValue(
    /data-icon="headset"/,
  );
  await expect(page.getByLabel("Script de integración")).toHaveValue(
    /data-primary-color="#104957"/,
  );
  await page.goto(`/preview?chatbot_id=${ids[0]}&color=%23104957&icon=headset`);
  await page.getByRole("button", { name: "Abrir asistente BIDACHAT" }).click();
  await expect(page.locator("bidachat-widget .avatar svg rect")).toHaveCount(2);
  await expect(page.locator("bidachat-widget")).toHaveAttribute("style", /#104957/);
});

for (const theme of ["light", "dark"] as const) {
  test(`appearance proposals are accessible and responsive in ${theme}`, async ({
    page,
  }) => {
    await prepare(page, { theme });
    await page.goto(`/?view=Chatbots&edit=${ids[0]}&step=1`);
    await page.getByRole("radio", { name: "Azul", exact: true }).check();
    await page.getByRole("radio", { name: "Conocimiento", exact: true }).check();
    for (const width of [1440, 1089, 390, 320]) {
      await page.setViewportSize({ width, height: width < 500 ? 844 : 900 });
      await expect(
        page
          .frameLocator("iframe[title='Vista visual del chatbot']")
          .locator("bidachat-widget"),
      ).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      ).toBeTruthy();
      await expect(
        page.getByRole("radio", { name: "Azul", exact: true }),
      ).toBeChecked();
      const audit = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect(audit.violations).toEqual([]);
      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement)
          document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.mouse.move(0, 0);
      await page.screenshot({
        path: `${process.env.APPEARANCE_CAPTURE_DIR ?? "../docs/qa/frontend/appearance"}/${theme}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
    }
  });
}
