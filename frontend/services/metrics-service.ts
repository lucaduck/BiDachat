import { request } from "@/services/api-client";
import type { MetricsInterval, MetricsStatus } from "./metrics-filters";
import type { MetricsSummary } from "@/types/api";

export function getMetrics(
  token: string,
  chatbotId: string,
  startedAt?: string,
  endedAt?: string,
  options?: {
    interval: MetricsInterval;
    status: MetricsStatus;
    includeSeries: boolean;
  },
) {
  const parameters = new URLSearchParams();
  if (startedAt && endedAt) {
    parameters.set("started_at", startedAt);
    parameters.set("ended_at", endedAt);
  }
  if (options) {
    parameters.set("interval", options.interval);
    if (options.status !== "all") parameters.set("query_status", options.status);
    parameters.set("include_series", String(options.includeSeries));
  }
  const suffix = parameters.size ? `?${parameters.toString()}` : "";
  return request<MetricsSummary>(`/chatbots/${chatbotId}/metrics${suffix}`, { token });
}
