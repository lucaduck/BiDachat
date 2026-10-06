export type MetricsPeriod = "all" | "7" | "30" | "90" | "custom";
export type MetricsInterval = "day" | "week" | "month";
export type MetricsStatus = "all" | "completed" | "failed" | "processing";
export type MetricsFilters = {
  period: MetricsPeriod;
  interval: MetricsInterval;
  status: MetricsStatus;
  startDate: string;
  endDate: string;
};
export function isCalendarDate(value: string) {
  return (
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(`${value}T00:00:00Z`)) &&
    new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value
  );
}
export function metricsDateRange(filters: MetricsFilters, now = new Date()) {
  if (filters.period === "all") return {};
  if (filters.period === "custom") {
    if (
      !isCalendarDate(filters.startDate) ||
      !isCalendarDate(filters.endDate) ||
      filters.startDate > filters.endDate
    )
      throw new Error("Selecciona una fecha inicial y final válidas, en ese orden.");
    const end = new Date(`${filters.endDate}T00:00:00Z`);
    end.setUTCDate(end.getUTCDate() + 1);
    return {
      startedAt: `${filters.startDate}T00:00:00.000Z`,
      endedAt: end.toISOString(),
    };
  }
  // Include today's partial UTC day and the preceding calendar days.
  const start = new Date(now);
  start.setUTCHours(0, 0, 0, 0);
  start.setUTCDate(start.getUTCDate() - Number(filters.period) + 1);
  return { startedAt: start.toISOString(), endedAt: now.toISOString() };
}
