import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
// @ts-expect-error JavaScript fixture shared with the workspace acceptance tests.
import { prepare } from "./fixtures.mjs";

for (const theme of ["light", "dark"] as const) {
  test(`circuit panel uses real activity and supplied branding in ${theme}`, async ({
    page,
  }) => {
    await prepare(page, { theme });
    await page.goto("/?view=Chatbots");
    await expect(
      page.locator(".chatbot-activity-card").first().locator("dd").first(),
    ).toHaveText("20");
    await expect(
      page.locator(".chatbot-activity-card").nth(1).locator("dd").first(),
    ).toHaveText("16");
    await expect(
      page.locator(".chatbot-activity-card").nth(2).locator("dd").first(),
    ).toHaveText("2");
    await expect(
      page.locator(".chatbot-card-activity").first().locator("dd").first(),
    ).toHaveText("12");
    await expect(page.locator(".workspace-brand-banner")).toContainText(
      "Hacia la transformación digital",
    );
    await expect
      .poll(() =>
        page
          .locator(".sidebar .brand img:visible")
          .evaluate((image) => (image as HTMLImageElement).naturalWidth),
      )
      .toBeGreaterThan(0);
    for (const width of [1440, 1310, 1089, 390, 320]) {
      await page.setViewportSize({
        width,
        height: width === 1310 ? 740 : width < 500 ? 844 : 900,
      });
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      ).toBeTruthy();
      await expect(page.locator(".workspace-motto")).toBeVisible();
      expect(
        await page
          .locator(".workspace-motto")
          .evaluate((element) => getComputedStyle(element).fontFamily),
      ).toContain("Caveat");
      if (width > 768) {
        await expect(page.locator(".sidebar-watermark")).toBeVisible();
        await expect(page.locator(".workspace-motto")).toContainText("Datos que");
      }
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
        path: `${process.env.PANEL_CAPTURE_DIR ?? "../docs/qa/frontend/panel-branding"}/${theme}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
    }
  });
}

test("panel activity failures recover and the create tile works", async ({ page }) => {
  await prepare(page);
  await page.route("**/api/v1/chatbots/*/metrics", (route) =>
    route.fulfill({ status: 503, json: { detail: "Fixture service unavailable" } }),
  );
  await page.goto("/?view=Chatbots");
  await expect(
    page.getByText("No se pudo cargar la actividad.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.locator(".chatbot-activity-card").first().locator("dd").first(),
  ).toHaveText("—");
  await page.unroute("**/api/v1/chatbots/*/metrics");
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(
    page.locator(".chatbot-activity-card").first().locator("dd").first(),
  ).toHaveText("20");
  await page.getByRole("button", { name: "Crear nuevo chatbot", exact: false }).click();
  await expect(page.getByLabel("Nombre del chatbot")).toBeVisible();
  await expect(page).toHaveURL(/mode=create/);
});

test("mobile navigation remains below the logo and does not overlap logout", async ({
  page,
}) => {
  await prepare(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?view=Chatbots");
  await page.getByRole("button", { name: "Menú", exact: true }).click();
  const brand = await page.locator(".sidebar-heading").boundingBox();
  const navigation = await page.locator(".sidebar-nav").boundingBox();
  const footer = await page.locator(".sidebar-footer").boundingBox();
  expect(navigation!.y).toBeGreaterThanOrEqual(brand!.y + brand!.height);
  expect(footer!.y).toBeGreaterThanOrEqual(navigation!.y + navigation!.height);
});

test("theme switch swaps both exact circuit logo files and persists on refresh", async ({
  page,
}) => {
  await prepare(page, { theme: "light" });
  await page.goto("/?view=Chatbots");
  for (const root of [".sidebar .brand", ".banner-brand"])
    await expect(page.locator(`${root} img:visible`)).toHaveAttribute(
      "src",
      /logo-bc-circuit-light/,
    );
  await page.getByRole("button", { name: "Activar modo oscuro" }).click();
  for (const root of [".sidebar .brand", ".banner-brand"])
    await expect(page.locator(`${root} img:visible`)).toHaveAttribute(
      "src",
      /logo-bc-circuit.png/,
    );
  await page.reload();
  await expect(page.locator(".sidebar .brand img:visible")).toHaveAttribute(
    "src",
    /logo-bc-circuit.png/,
  );
  await page.getByRole("button", { name: "Activar modo claro" }).click();
  await expect(page.locator(".sidebar .brand img:visible")).toHaveAttribute(
    "src",
    /logo-bc-circuit-light/,
  );
});
