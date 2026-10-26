import { request } from "@/services/api-client";
import type { MetricsInterval } from "@/services/metrics-filters";
import type { SatisfactionMetrics, SurveyCommentsPage } from "@/types/api";

function filterQuery(startedAt?: string, endedAt?: string, interval?: MetricsInterval) {
  const parameters = new URLSearchParams();
  if (startedAt && endedAt) {
    parameters.set("started_at", startedAt);
    parameters.set("ended_at", endedAt);
  }
  if (interval) parameters.set("interval", interval);
  return parameters;
}

export function getSatisfactionMetrics(
  token: string,
  chatbotId: string,
  startedAt?: string,
  endedAt?: string,
  interval: MetricsInterval = "day",
) {
  const parameters = filterQuery(startedAt, endedAt, interval);
  return request<SatisfactionMetrics>(
    `/chatbots/${chatbotId}/satisfaction-metrics?${parameters.toString()}`,
    { token },
  );
}

export function getSurveyComments(
  token: string,
  chatbotId: string,
  startedAt?: string,
  endedAt?: string,
  offset = 0,
) {
  const parameters = filterQuery(startedAt, endedAt);
  parameters.set("offset", String(offset));
  parameters.set("limit", "10");
  return request<SurveyCommentsPage>(
    `/chatbots/${chatbotId}/survey-responses?${parameters.toString()}`,
    { token },
  );
}
