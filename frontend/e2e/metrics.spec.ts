import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
// @ts-expect-error Shared JavaScript fixture.
import { prepare, ids, metrics, satisfaction } from "./fixtures.mjs";

test("satisfaction uses the same period and chatbot, with safe administrative comments", async ({
  page,
}) => {
  await prepare(page);
  const requests: URL[] = [];
  await page.route("**/api/v1/chatbots/*/satisfaction-metrics?*", (route) => {
    const url = new URL(route.request().url());
    requests.push(url);
    const data = satisfaction(url.pathname.includes(ids[1]) ? ids[1] : ids[0]);
    Object.assign(data, {
      offers: 4,
      responses: 2,
      satisfied: 1,
      participation_rate: 0.5,
      csat_rate: 0.5,
      clarity_count: 1,
      average_clarity: 5,
      resolution_count: 1,
      resolved: 1,
      resolution_rate: 1,
      scores: { 1: 0, 2: 1, 3: 0, 4: 1, 5: 0 },
      series: [
        {
          period_start: "2026-10-01T00:00:00Z",
          offers: 4,
          responses: 2,
          satisfied: 1,
          clarity_count: 1,
          clarity_sum: 5,
          resolution_count: 1,
          resolved: 1,
          scores: { 1: 0, 2: 1, 3: 0, 4: 1, 5: 0 },
        },
      ],
    });
    return route.fulfill({ json: data });
  });
  await page.route("**/api/v1/chatbots/*/survey-responses?*", (route) =>
    route.fulfill({
      json: {
        items: [
          { submitted_at: "2026-10-01T12:00:00Z", comment: "<script>texto</script>" },
        ],
        total: 1,
        limit: 10,
        offset: 0,
      },
    }),
  );
  await page.goto("/?view=M%C3%A9tricas");
  await expect(
    page.getByRole("heading", { name: "Satisfacción de visitantes" }),
  ).toBeVisible();
  await expect(page.locator(".satisfaction-section .metric-card").nth(2)).toContainText(
    "50 %",
  );
  await page.getByText("Ver datos por periodo").click();
  await expect(page.locator(".satisfaction-section tbody tr")).toHaveCount(1);
  await expect(page.locator(".survey-comments script")).toHaveCount(0);
  await expect(page.locator(".survey-comments")).toContainText(
    "<script>texto</script>",
  );
  await page.getByLabel("Estado", { exact: true }).selectOption("failed");
  await expect.poll(() => requests.length).toBeGreaterThan(1);
  expect(requests.at(-1)?.searchParams.has("query_status")).toBe(false);
  await page.getByLabel("Periodo", { exact: true }).selectOption("7");
  await expect.poll(() => requests.at(-1)?.searchParams.has("started_at")).toBe(true);
  await page.getByLabel("Chatbot", { exact: true }).selectOption(ids[1]);
  await expect.poll(() => requests.at(-1)?.pathname.includes(ids[1])).toBe(true);
});

test("functional chatbot preview offers the same survey after a completed answer", async ({
  page,
}) => {
  await prepare(page);
  let offered = 0;
  await page.route("**/api/v1/chatbots/*/survey-offers", (route) => {
    offered += 1;
    return route.fulfill({ json: { state: "offered" } });
  });
  await page.goto(`/preview?chatbot_id=${ids[0]}`);
  await page.locator("bidachat-widget .launcher").click();
  await expect(page.locator("bidachat-widget .finish-conversation")).toBeHidden();
  await page.locator("bidachat-widget .question").fill("¿Cómo va el tablero?");
  await page.locator("bidachat-widget .send").click();
  await expect(page.locator("bidachat-widget .finish-conversation")).toBeVisible();
  await page.locator("bidachat-widget .finish-conversation").click();
  await expect(page.locator("bidachat-widget .survey")).toBeVisible();
  expect(offered).toBe(1);
});

for (const theme of ["light", "dark"] as const) {
  test(`metrics charts and data table remain readable in ${theme}`, async ({
    page,
  }) => {
    await prepare(page, { theme });
    await page.goto("/?view=M%C3%A9tricas");
    await expect(page.locator(".metric-card").first().locator("dd")).toHaveText("12");
    await expect(
      page.getByRole("heading", { name: "Consultas por periodo" }),
    ).toBeVisible();
    await expect(page.locator(".metrics-bar")).toHaveCount(3);
    await expect(page.locator(".metrics-point")).toHaveCount(2);
    for (const width of [1440, 1089, 390, 320]) {
      await page.setViewportSize({ width, height: width < 500 ? 844 : 900 });
      await page.evaluate(() => document.fonts.ready);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      ).toBeTruthy();
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement)
          document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.mouse.move(0, 0);
      await page.screenshot({
        path: `${process.env.METRICS_CAPTURE_DIR ?? "../docs/qa/frontend/metrics"}/${theme}-${width}.png`,
        fullPage: true,
        animations: "disabled",
      });
    }
    await page.getByText("Ver tabla de datos (3 periodos)", { exact: true }).click();
    await expect(page.getByRole("table")).toBeVisible();
    await expect(page.getByRole("table").locator("tbody tr").nth(1)).toContainText(
      "No disponible",
    );
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  });
}

test("filters use API date boundaries and survive refresh without submitting invalid dates", async ({
  page,
}) => {
  await prepare(page);
  const requests: URL[] = [];
  await page.route("**/api/v1/chatbots/*/metrics?*", async (route) => {
    const url = new URL(route.request().url());
    requests.push(url);
    const status = url.searchParams.get("query_status");
    const data = metrics(url.pathname.includes(ids[1]) ? ids[1] : ids[0]);
    data.started_at = url.searchParams.get("started_at");
    data.ended_at = url.searchParams.get("ended_at");
    data.interval = url.searchParams.get("interval");
    if (status === "failed") {
      Object.assign(data, {
        total_queries: 1,
        completed_queries: 0,
        processing_queries: 0,
        measured_response_count: 0,
        average_response_time_ms: null,
        status,
      });
      data.series = data.series.map((point: { failed_queries: number }) => ({
        ...point,
        total_queries: point.failed_queries,
        completed_queries: 0,
        processing_queries: 0,
        measured_response_count: 0,
        average_response_time_ms: null,
      }));
    }
    await route.fulfill({ json: data });
  });
  await page.goto("/?view=M%C3%A9tricas");
  await page.getByLabel("Periodo", { exact: true }).selectOption("90");
  await expect.poll(() => requests.at(-1)?.searchParams.get("started_at")).toBeTruthy();
  await page.getByLabel("Estado", { exact: true }).selectOption("failed");
  await expect(page.locator(".metric-card").first().locator("dd")).toHaveText("1");
  await page.getByLabel("Agrupar por").selectOption("week");
  await expect.poll(() => requests.at(-1)?.searchParams.get("interval")).toBe("week");
  await page.getByLabel("Periodo", { exact: true }).selectOption("custom");
  await page.getByLabel("Desde", { exact: true }).fill("2026-10-03");
  await page.getByLabel("Hasta", { exact: true }).fill("2026-10-01");
  const count = requests.length;
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page.locator(".alert-error")).toContainText("fecha inicial");
  expect(requests).toHaveLength(count);
  await page.getByLabel("Desde", { exact: true }).fill("2026-10-01");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect
    .poll(() => requests.at(-1)?.searchParams.get("ended_at"))
    .toBe("2026-10-02T00:00:00.000Z");
  expect(requests.at(-1)?.searchParams.get("started_at")).toBe(
    "2026-10-01T00:00:00.000Z",
  );
  expect(requests.at(-1)?.searchParams.get("include_series")).toBe("true");
  await page.reload();
  await expect(page.getByLabel("Periodo", { exact: true })).toHaveValue("custom");
  await expect(page.getByLabel("Desde", { exact: true })).toHaveValue("2026-10-01");
  await expect(page.getByLabel("Agrupar por")).toHaveValue("week");
  await expect(page.getByLabel("Estado", { exact: true })).toHaveValue("failed");
  await page.getByLabel("Chatbot", { exact: true }).selectOption(ids[1]);
  await expect(page).toHaveURL(new RegExp(`chatbot_id=${ids[1]}`));
  await page.getByRole("button", { name: "Actualizar", exact: true }).click();
  await expect(page.locator(".metric-card").first().locator("dd")).toHaveText("1");
});

test("metrics failures recover and empty data never invents response times", async ({
  page,
}) => {
  await prepare(page);
  let failed = true;
  await page.route("**/api/v1/chatbots/*/metrics?*", (route) =>
    failed
      ? route.fulfill({ status: 503, json: { detail: "Fixture unavailable" } })
      : route.fulfill({
          json: {
            ...metrics(ids[0]),
            total_queries: 0,
            completed_queries: 0,
            failed_queries: 0,
            processing_queries: 0,
            measured_response_count: 0,
            average_response_time_ms: null,
            series: [],
          },
        }),
  );
  await page.goto("/?view=M%C3%A9tricas");
  await expect(page.locator(".alert-error")).toContainText("No se pudieron cargar");
  failed = false;
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.locator(".metric-card").first().locator("dd")).toHaveText("0");
  await expect(page.locator(".metric-card").nth(2).locator("dd")).toHaveText(
    "No disponible",
  );
  await expect(page.locator(".alert-error")).toHaveCount(0);
  await expect(page.locator(".metrics-timeline")).toHaveCount(0);
});
