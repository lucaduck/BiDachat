import { useEffect, useState } from "react";
import { Icon, type IconName } from "@/components/ui/icon";
import { Alert } from "@/components/ui/status";
import { getMetrics } from "@/services/metrics-service";
import type { Chatbot, MetricsSummary } from "@/types/api";

export function useChatbotActivity(
  chatbots: Chatbot[],
  token: string,
  onApiError: (error: unknown) => void,
  enabled: boolean,
) {
  const [records, setRecords] = useState<Record<string, MetricsSummary> | null>(null);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    async function loadActivity() {
      setRecords(null);
      setError(false);
      try {
        const results = await Promise.all(
          chatbots.map(
            async (chatbot) =>
              [chatbot.id, await getMetrics(token, chatbot.id)] as const,
          ),
        );
        if (active) setRecords(Object.fromEntries(results));
      } catch (requestError) {
        if (!active) return;
        onApiError(requestError);
        setError(true);
      }
    }
    void loadActivity();
    return () => {
      active = false;
    };
  }, [chatbots, token, onApiError, enabled, reloadKey]);
  return { records, error, reload: () => setReloadKey((value) => value + 1) };
}

export function ChatbotActivity({
  records,
  chatbotCount,
  error,
  reload,
}: Readonly<{
  records: Record<string, MetricsSummary> | null;
  chatbotCount: number;
  error: boolean;
  reload: () => void;
}>) {
  const metrics = Object.values(records ?? {});
  const count = (key: "total_queries" | "completed_queries" | "failed_queries") =>
    records
      ? metrics.reduce((total, item) => total + item[key], 0).toLocaleString("es-EC")
      : error
        ? "—"
        : "…";
  const cards: { label: string; value: string; icon: IconName }[] = [
    { label: "Consultas totales", value: count("total_queries"), icon: "message" },
    {
      label: "Consultas completadas",
      value: count("completed_queries"),
      icon: "check",
    },
    { label: "Consultas con error", value: count("failed_queries"), icon: "chart" },
    { label: "Chatbots configurados", value: String(chatbotCount), icon: "bot" },
  ];
  return (
    <>
      {error ? (
        <Alert tone="warning">
          No se pudo cargar la actividad.{" "}
          <button type="button" className="text-action" onClick={reload}>
            Reintentar
          </button>
        </Alert>
      ) : null}
      <dl
        className="chatbot-activity-grid"
        aria-label="Actividad acumulada de los chatbots"
        aria-busy={!records && !error}
      >
        {cards.map(({ label, value, icon }) => (
          <div className="chatbot-activity-card" key={label}>
            <dt>
              <Icon name={icon} />
              {label}
            </dt>
            <dd>{value}</dd>
            <dd className="activity-caption">Datos acumulados</dd>
          </div>
        ))}
      </dl>
    </>
  );
}
