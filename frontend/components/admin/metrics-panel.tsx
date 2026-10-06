"use client";

import { useEffect, useState } from "react";
import { InputField, SelectField } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Alert, EmptyState, LoadingState } from "@/components/ui/status";
import { getMetrics } from "@/services/metrics-service";
import { metricsDateRange, type MetricsFilters } from "@/services/metrics-filters";
import type { Chatbot, MetricsSummary } from "@/types/api";
import { MetricsCharts, formatMetricTime } from "./metrics-charts";
import "./metrics.css";

type Props = {
  initialChatbotId?: string;
  initialFilters: MetricsFilters;
  onFilterChange: (chatbotId: string, filters: MetricsFilters) => void;
  chatbots: Chatbot[];
  token: string;
  onApiError: (error: unknown) => void;
};
export function MetricsPanel({
  chatbots,
  token,
  onApiError,
  initialChatbotId,
  initialFilters,
  onFilterChange,
}: Readonly<Props>) {
  const chatbotId = chatbots.some((bot) => bot.id === initialChatbotId)
    ? initialChatbotId!
    : (chatbots[0]?.id ?? "");
  const [draft, setDraft] = useState(initialFilters);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [error, setError] = useState(false);
  const [validation, setValidation] = useState(() => {
    try {
      metricsDateRange(initialFilters);
      return "";
    } catch (rangeError) {
      return (rangeError as Error).message;
    }
  });
  const [reloadKey, setReloadKey] = useState(0);
  const { period, interval, status, startDate, endDate } = initialFilters;
  useEffect(() => {
    if (!chatbotId) return;
    let active = true;
    let range: ReturnType<typeof metricsDateRange>;
    try {
      range = metricsDateRange({ period, interval, status, startDate, endDate });
    } catch {
      return;
    }
    getMetrics(token, chatbotId, range.startedAt, range.endedAt, {
      interval,
      status,
      includeSeries: true,
    })
      .then((result) => {
        if (active) {
          setMetrics(result);
          setError(false);
        }
      })
      .catch((requestError) => {
        if (active) {
          onApiError(requestError);
          setError(true);
        }
      });
    return () => {
      active = false;
    };
  }, [
    chatbotId,
    onApiError,
    period,
    interval,
    status,
    startDate,
    endDate,
    reloadKey,
    token,
  ]);

  function applyFilters(next: MetricsFilters, selectedId = chatbotId) {
    try {
      metricsDateRange(next);
    } catch (rangeError) {
      setValidation((rangeError as Error).message);
      return;
    }
    setValidation("");
    setDraft(next);
    onFilterChange(selectedId, next);
  }
  function updateFilter(key: "period" | "interval" | "status", value: string) {
    const next = { ...draft, [key]: value } as MetricsFilters;
    setDraft(next);
    setValidation("");
    if (next.period !== "custom") applyFilters(next);
  }
  if (!chatbots.length)
    return (
      <EmptyState
        title="No hay chatbots"
        description="Crea un chatbot para consultar sus métricas."
      />
    );
  return (
    <section aria-label="Métricas">
      <div className="section-heading">
        <div>
          <h2>Métricas de uso</h2>
          <p>Consulta la actividad y los tiempos de respuesta de tus asistentes.</p>
        </div>
        <Button
          variant="secondary"
          disabled={!metrics && !error}
          onClick={() => {
            setMetrics(null);
            setError(false);
            setReloadKey((key) => key + 1);
          }}
        >
          <Icon name="refresh" />
          Actualizar
        </Button>
      </div>
      <form
        className="metrics-filters"
        onSubmit={(event) => {
          event.preventDefault();
          applyFilters(draft);
        }}
      >
        <SelectField
          id="metrics-chatbot"
          label="Chatbot"
          value={chatbotId}
          onChange={(event) => applyFilters(initialFilters, event.target.value)}
        >
          {chatbots.map((bot) => (
            <option key={bot.id} value={bot.id}>
              {bot.name}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="metrics-period"
          label="Periodo"
          value={draft.period}
          onChange={(event) => updateFilter("period", event.target.value)}
        >
          <option value="all">Todo el historial</option>
          <option value="7">Últimos 7 días</option>
          <option value="30">Últimos 30 días</option>
          <option value="90">Últimos 90 días</option>
          <option value="custom">Fechas personalizadas</option>
        </SelectField>
        <SelectField
          id="metrics-status"
          label="Estado"
          value={draft.status}
          onChange={(event) => updateFilter("status", event.target.value)}
        >
          <option value="all">Todos los estados</option>
          <option value="completed">Completadas</option>
          <option value="failed">Fallidas</option>
          <option value="processing">En proceso</option>
        </SelectField>
        <SelectField
          id="metrics-interval"
          label="Agrupar por"
          value={draft.interval}
          onChange={(event) => updateFilter("interval", event.target.value)}
        >
          <option value="day">Día</option>
          <option value="week">Semana</option>
          <option value="month">Mes</option>
        </SelectField>
        {draft.period === "custom" ? (
          <>
            <InputField
              id="metrics-start"
              label="Desde"
              type="date"
              required
              value={draft.startDate}
              onChange={(event) => {
                setDraft({ ...draft, startDate: event.target.value });
                setValidation("");
              }}
            />
            <InputField
              id="metrics-end"
              label="Hasta"
              type="date"
              required
              value={draft.endDate}
              onChange={(event) => {
                setDraft({ ...draft, endDate: event.target.value });
                setValidation("");
              }}
            />
            <Button type="submit">Aplicar filtros</Button>
          </>
        ) : null}
        <p className="metrics-filter-hint">
          Fechas en UTC. El rango personalizado incluye ambos días. Para historiales
          extensos, agrupa por semana o mes.
        </p>
        {validation ? (
          <div className="metrics-filter-error">
            <Alert tone="error">{validation}</Alert>
          </div>
        ) : null}
      </form>
      {error ? (
        <Alert tone="error">
          No se pudieron cargar las métricas. Si el historial supera 1000 periodos,
          selecciona una agrupación mayor o acota las fechas.{" "}
          <button
            className="text-action"
            type="button"
            onClick={() => {
              setError(false);
              setMetrics(null);
              setReloadKey((key) => key + 1);
            }}
          >
            Reintentar
          </button>
        </Alert>
      ) : null}
      {!error && !metrics && !validation ? (
        <LoadingState label="Cargando métricas…" />
      ) : null}
      {metrics ? (
        <>
          <p className="metrics-filter-hint" aria-live="polite">
            {metrics.total_queries === 0
              ? "No hay consultas para los filtros aplicados."
              : `${metrics.total_queries.toLocaleString("es-EC")} consultas en los filtros aplicados.`}
            {JSON.stringify(draft) !== JSON.stringify(initialFilters)
              ? " Hay cambios pendientes. Pulsa «Aplicar filtros» para consultar las nuevas fechas."
              : ""}
          </p>
          <p className="metrics-filter-hint">
            {metrics.started_at && metrics.ended_at
              ? `Rango aplicado (UTC): ${metrics.started_at.slice(0, 10)} — ${new Date(new Date(metrics.ended_at).getTime() - 1).toISOString().slice(0, 10)}`
              : "Rango aplicado: todo el historial"}
          </p>
          <dl className="metric-grid">
            <div className="metric-card">
              <dt>
                <Icon name="chart" className="metric-icon" />
                Consultas
              </dt>
              <dd>{metrics.total_queries.toLocaleString("es-EC")}</dd>
            </div>
            <div className="metric-card">
              <dt>
                <Icon name="check" className="metric-icon" />
                Completadas
              </dt>
              <dd>{metrics.completed_queries.toLocaleString("es-EC")}</dd>
            </div>
            <div className="metric-card">
              <dt>
                <Icon name="dashboard" className="metric-icon" />
                Tiempo medio de respuesta
              </dt>
              <dd>{formatMetricTime(metrics.average_response_time_ms)}</dd>
            </div>
            <div className="metric-card">
              <dt>
                <Icon name="close" className="metric-icon" />
                Fallidas
              </dt>
              <dd>{metrics.failed_queries.toLocaleString("es-EC")}</dd>
            </div>
          </dl>
          <MetricsCharts metrics={metrics} />
        </>
      ) : null}
    </section>
  );
}
