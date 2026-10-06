import {
  isCalendarDate,
  type MetricsPeriod,
  type MetricsInterval,
  type MetricsStatus,
} from "@/services/metrics-filters";
export const WORKSPACE_VIEWS = [
  "Resumen",
  "Chatbots",
  "Documentos",
  "Métricas",
  "Configuración",
] as const;
export type WorkspaceView = (typeof WORKSPACE_VIEWS)[number];
export const EDITOR_STEPS = [
  "General",
  "Apariencia",
  "Comportamiento",
  "Conocimiento",
  "Publicación",
] as const;
export const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export type WorkspaceRoute = {
  view: WorkspaceView;
  editId?: string;
  creating?: boolean;
  step: number;
  chatbotId?: string;
  period?: MetricsPeriod;
  interval?: MetricsInterval;
  status?: MetricsStatus;
  startDate?: string;
  endDate?: string;
  invalid?: boolean;
};
export function parseWorkspaceRoute(search: string): WorkspaceRoute {
  const params = new URLSearchParams(search);
  const rawView = params.get("view");
  const view = WORKSPACE_VIEWS.find((value) => value === rawView) ?? "Resumen";
  const edit = params.get("edit");
  const rawStep = params.get("step");
  const step = rawStep === null ? 0 : Number(rawStep);
  const id = params.get("chatbot_id");
  const period = params.get("period");
  const interval = params.get("interval");
  const status = params.get("status");
  const startDate = params.get("start_date");
  const endDate = params.get("end_date");
  const invalid = Boolean(
    (rawView && !WORKSPACE_VIEWS.includes(rawView as WorkspaceView)) ||
      (edit && !UUID_PATTERN.test(edit)) ||
      (id && !UUID_PATTERN.test(id)) ||
      (rawStep !== null && !/^[0-4]$/.test(rawStep)) ||
      (params.has("mode") && params.get("mode") !== "create") ||
      (period && !["all", "7", "30", "90", "custom"].includes(period)) ||
      (interval && !["day", "week", "month"].includes(interval)) ||
      (status && !["all", "completed", "failed", "processing"].includes(status)) ||
      (startDate && !isCalendarDate(startDate)) ||
      (endDate && !isCalendarDate(endDate)) ||
      (period === "custom" && (!startDate || !endDate || startDate > endDate)),
  );
  return {
    view,
    step: invalid
      ? 0
      : params.get("mode") === "create" && !edit
        ? Math.min(step, 2)
        : step,
    editId: view === "Chatbots" && edit && UUID_PATTERN.test(edit) ? edit : undefined,
    creating: view === "Chatbots" && params.get("mode") === "create" && !edit,
    chatbotId: id && UUID_PATTERN.test(id) ? id : undefined,
    period:
      period && ["all", "7", "30", "90", "custom"].includes(period)
        ? (period as WorkspaceRoute["period"])
        : undefined,
    interval:
      interval && ["day", "week", "month"].includes(interval)
        ? (interval as MetricsInterval)
        : undefined,
    status:
      status && ["all", "completed", "failed", "processing"].includes(status)
        ? (status as MetricsStatus)
        : undefined,
    startDate: startDate && isCalendarDate(startDate) ? startDate : undefined,
    endDate: endDate && isCalendarDate(endDate) ? endDate : undefined,
    invalid,
  };
}
export function workspaceUrl(
  route: Partial<WorkspaceRoute> & { view: WorkspaceView },
): string {
  const params = new URLSearchParams();
  if (route.view !== "Resumen") params.set("view", route.view);
  if (route.view === "Chatbots") {
    if (route.editId && UUID_PATTERN.test(route.editId))
      params.set("edit", route.editId);
    else if (route.creating) params.set("mode", "create");
    if (
      (route.editId || route.creating) &&
      route.step &&
      route.step >= 0 &&
      route.step <= 4
    )
      params.set("step", String(route.step));
  }
  if (route.chatbotId && UUID_PATTERN.test(route.chatbotId))
    params.set("chatbot_id", route.chatbotId);
  if (route.period && ["all", "7", "30", "90", "custom"].includes(route.period))
    params.set("period", route.period);
  if (route.view === "Métricas") {
    if (route.interval) params.set("interval", route.interval);
    if (route.status) params.set("status", route.status);
    if (route.period === "custom") {
      if (route.startDate) params.set("start_date", route.startDate);
      if (route.endDate) params.set("end_date", route.endDate);
    }
  }
  return params.size ? `/?${params}` : "/";
}
export function safeWorkspaceReturn(value: string): string {
  try {
    const url = new URL(value, "https://bidachat.invalid");
    if (url.origin !== "https://bidachat.invalid" || url.pathname !== "/") return "/";
    const route = parseWorkspaceRoute(url.search);
    return route.invalid ? "/" : workspaceUrl(route);
  } catch {
    return "/";
  }
}
