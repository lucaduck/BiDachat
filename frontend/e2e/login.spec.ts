import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
// @ts-expect-error JavaScript fixture shared with the workspace acceptance tests.
import { prepare } from "./fixtures.mjs";

for (const theme of ["light", "dark"] as const) {
  test(`login reference layout and supplied logo in ${theme}`, async ({ page }) => {
    await prepare(page, { authenticated: false, theme });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
    const logo = page.getByRole("img", { name: /BIDACHAT.*Gestor de chatbots/ });
    await expect(logo).toBeVisible();
    await expect(logo).toHaveAttribute(
      "src",
      new RegExp(theme === "dark" ? "login-logo-dark" : "logo-bidachat-light"),
    );
    await expect
      .poll(() => logo.evaluate((image) => (image as HTMLImageElement).naturalWidth))
      .toBeGreaterThan(0);
    for (const width of [1440, 1089, 768, 390, 320]) {
      await page.setViewportSize({ width, height: width < 500 ? 844 : 900 });
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      ).toBeTruthy();
      await expect(page.getByLabel("Correo institucional")).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Iniciar sesión", exact: true }),
      ).toBeVisible();
      await page.screenshot({
        path: `${process.env.LOGIN_CAPTURE_DIR ?? "../docs/qa/frontend/login"}/${theme}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
      if (width === 1440 || width === 320) {
        const audit = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        expect(audit.violations).toEqual([]);
      }
    }
  });
}

test("login theme persistence, credential errors and return destination", async ({
  page,
  context,
}) => {
  await prepare(page, { authenticated: false });
  await page.goto("/?view=Chatbots");
  await page.getByRole("button", { name: "Cambiar a modo oscuro" }).click();
  const restoredPage = await context.newPage();
  await restoredPage.goto("/");
  await restoredPage.reload();
  await expect(
    restoredPage.getByRole("button", { name: "Cambiar a modo claro" }),
  ).toBeVisible();
  await expect(restoredPage.locator("html")).toHaveAttribute("data-theme", "dark");
  await restoredPage.close();
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await expect(page.getByLabel("Correo institucional")).toBeFocused();
  await page.getByLabel("Correo institucional").fill("qa@example.test");
  await page.getByLabel("Contraseña", { exact: true }).fill("qa-password");
  await page.getByRole("button", { name: "Mostrar contraseña" }).click();
  await expect(page.getByLabel("Contraseña", { exact: true })).toHaveAttribute(
    "type",
    "text",
  );
  await page.getByRole("button", { name: "Ocultar contraseña" }).click();
  await page.route("**/api/v1/auth/login", (route) =>
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Credenciales inválidas" }),
    }),
  );
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await expect(page.locator(".login-form-panel").getByRole("alert")).toContainText(
    "Verifica tus credenciales",
  );
  await expect(page.getByLabel("Correo institucional")).toHaveValue("qa@example.test");
  await expect(page.getByLabel("Contraseña", { exact: true })).toHaveValue(
    "qa-password",
  );
  await page.unroute("**/api/v1/auth/login");
  await page.getByRole("button", { name: "Iniciar sesión", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mis chatbots" })).toBeVisible();
  await expect(page).toHaveURL(/view=Chatbots/);
});
