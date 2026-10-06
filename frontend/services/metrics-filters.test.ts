import { describe, expect, it } from "vitest";
import {
  isCalendarDate,
  metricsDateRange,
  type MetricsFilters,
} from "./metrics-filters";
const filters: MetricsFilters = {
  period: "custom",
  interval: "day",
  status: "all",
  startDate: "2026-01-31",
  endDate: "2026-02-02",
};
describe("metrics date filters", () => {
  it("includes the final UTC calendar day while keeping API boundaries exclusive", () => {
    expect(metricsDateRange(filters)).toEqual({
      startedAt: "2026-01-31T00:00:00.000Z",
      endedAt: "2026-02-03T00:00:00.000Z",
    });
    expect(metricsDateRange({ ...filters, endDate: filters.startDate }).endedAt).toBe(
      "2026-02-01T00:00:00.000Z",
    );
  });
  it("rejects missing, impossible and inverted dates", () => {
    expect(isCalendarDate("2026-02-30")).toBe(false);
    for (const pair of [
      ["", "2026-02-02"],
      ["2026-02-30", "2026-03-01"],
      ["2026-02-03", "2026-02-02"],
    ])
      expect(() =>
        metricsDateRange({ ...filters, startDate: pair[0], endDate: pair[1] }),
      ).toThrow();
  });
  it("quick periods include today's partial UTC day and no future time", () => {
    const now = new Date("2026-10-06T18:30:00Z");
    expect(metricsDateRange({ ...filters, period: "7" }, now)).toEqual({
      startedAt: "2026-09-30T00:00:00.000Z",
      endedAt: now.toISOString(),
    });
    expect(metricsDateRange({ ...filters, period: "all" }, now)).toEqual({});
  });
});
