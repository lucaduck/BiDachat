import { describe, expect, it } from "vitest";
import { parseWorkspaceRoute, workspaceUrl, safeWorkspaceReturn } from "./navigation";
const id = "42e590ec-0def-4ea7-8e4b-b03d1557c1b9";
describe("workspace navigation", () => {
  it("preserves metrics filters through reload links and rejects invalid ranges", () => {
    const route = {
      view: "Métricas" as const,
      chatbotId: id,
      period: "custom" as const,
      interval: "week" as const,
      status: "failed" as const,
      startDate: "2026-01-31",
      endDate: "2026-02-02",
    };
    expect(parseWorkspaceRoute(workspaceUrl(route).split("?")[1])).toMatchObject(route);
    for (const search of [
      "period=custom",
      "interval=year",
      "status=bad",
      "start_date=2026-02-30",
      "period=custom&start_date=2026-03-02&end_date=2026-03-01",
    ])
      expect(parseWorkspaceRoute(search).invalid).toBe(true);
  });
  it("round trips legacy editor links for all steps", () => {
    for (let step = 0; step < 5; step++) {
      const url = workspaceUrl({ view: "Chatbots", editId: id, step });
      expect(parseWorkspaceRoute(url.split("?")[1])).toMatchObject({
        view: "Chatbots",
        editId: id,
        step,
        invalid: false,
      });
    }
  });
  it("distinguishes creating and editing from malformed resources", () => {
    expect(parseWorkspaceRoute("view=Chatbots&mode=create").creating).toBe(true);
    for (const search of [
      "view=other",
      "view=Chatbots&edit=oops",
      "step=12",
      "period=999",
      "mode=other",
    ])
      expect(parseWorkspaceRoute(search).invalid).toBe(true);
    expect(workspaceUrl({ view: "Chatbots" })).toBe("/?view=Chatbots");
  });
  it("only allows local workspace return destinations", () => {
    for (const url of [
      "https://evil.test/",
      "//evil.test/",
      "javascript:alert(1)",
      "/preview",
      "/?view=bad",
    ])
      expect(safeWorkspaceReturn(url)).toBe("/");
    expect(safeWorkspaceReturn(`/?view=Chatbots&edit=${id}&step=3`)).toContain(
      "step=3",
    );
  });
});
