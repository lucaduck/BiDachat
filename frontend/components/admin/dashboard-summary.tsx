"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Alert, EmptyState, LoadingState } from "@/components/ui/status";
import { listDocuments } from "@/services/document-service";
import { getMetrics } from "@/services/metrics-service";
import { UsageCharts } from "./usage-charts";
import type { Chatbot, MetricsSummary } from "@/types/api";

type DashboardSummaryProps = {
  chatbots: Chatbot[];
  onApiError: (error: unknown) => void;
  onNavigate: (view: "Chatbots" | "Documentos" | "Métricas") => void;
  token: string;
};

type Summary = {
  documentCount: number;
  pendingDocuments: number;
  queryCount: number;
  records: { id: string; name: string; metrics: MetricsSummary }[];
  completed: number;
  failed: number;
  processing: number;
};

export function DashboardSummary({
  chatbots,
  onApiError,
  onNavigate,
  token,
}: Readonly<DashboardSummaryProps>) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    if (chatbots.length === 0) return;

    async function loadSummary() {
      setSummary(null);
      setError(false);
      try {
        const endedAt = new Date();
        const startedAt = new Date(endedAt);
        startedAt.setUTCDate(startedAt.getUTCDate() - 30);
        const records = await Promise.all(
          chatbots.map(async (chatbot) => {
            const [documents, metrics] = await Promise.all([
              listDocuments(token, chatbot.id),
              getMetrics(
                token,
                chatbot.id,
                startedAt.toISOString(),
                endedAt.toISOString(),
              ),
            ]);
            return { documents, metrics, id: chatbot.id, name: chatbot.name };
          }),
        );
        if (!active) return;
        setSummary({
          records: records.map(({ id, name, metrics }) => ({ id, name, metrics })),
          completed: records.reduce((n, r) => n + r.metrics.completed_queries, 0),
          failed: records.reduce((n, r) => n + r.metrics.failed_queries, 0),
          processing: records.reduce((n, r) => n + r.metrics.processing_queries, 0),
          documentCount: records.reduce(
            (total, record) => total + record.documents.length,
            0,
          ),
          pendingDocuments: records.reduce(
            (total, record) =>
              total +
              record.documents.filter(
                (document) =>
                  document.status === "pending" || document.status === "processing",
              ).length,
            0,
          ),
          queryCount: records.reduce(
            (total, record) => total + record.metrics.total_queries,
            0,
          ),
        });
      } catch (requestError) {
        if (!active) return;
        onApiError(requestError);
        setError(true);
      }
    }

    void loadSummary();
    return () => {
      active = false;
    };
  }, [chatbots, onApiError, reloadKey, token]);

  if (chatbots.length === 0) {
    return (
      <EmptyState
        title="Aún no hay chatbots"
        description="Crea un chatbot para asociar documentos y consultar su actividad."
        action={<Button onClick={() => onNavigate("Chatbots")}>Crear chatbot</Button>}
      />
    );
  }

  return (
    <div>
      {error ? (
        <Alert tone="error">
          No se pudieron cargar documentos y métricas.{" "}
          <Button variant="quiet" onClick={() => setReloadKey((key) => key + 1)}>
            Reintentar
          </Button>
        </Alert>
      ) : null}
      {!error && !summary ? (
        <LoadingState label="Cargando documentos y métricas…" />
      ) : null}
      {summary ? (
        <>
          <dl className="metric-grid">
            <div className="metric-card">
              <Icon name="bot" className="metric-icon" />
              <dt>Chatbots configurados</dt>
              <dd>{chatbots.length}</dd>
            </div>
            <div className="metric-card">
              <Icon name="upload" className="metric-icon" />
              <dt>Documentos pendientes</dt>
              <dd>
                {summary.pendingDocuments}
                <p>De {summary.documentCount} asociaciones de fuentes</p>
              </dd>
            </div>
            <div className="metric-card">
              <Icon name="chart" className="metric-icon" />
              <dt>Consultas en 30 días</dt>
              <dd>
                {summary.queryCount}
                <p>De todos los chatbots</p>
              </dd>
            </div>
            <div className="metric-card">
              <Icon name="file" className="metric-icon" />
              <dt>Asociaciones de fuentes</dt>
              <dd>
                {summary.documentCount}
                <p>Fuentes de conocimiento</p>
              </dd>
            </div>
          </dl>
          <UsageCharts
            records={summary.records}
            completed={summary.completed}
            failed={summary.failed}
            processing={summary.processing}
          />
          <div className="summary-actions">
            <Button variant="secondary" onClick={() => onNavigate("Chatbots")}>
              Gestionar chatbots
            </Button>
            <Button variant="secondary" onClick={() => onNavigate("Documentos")}>
              Ver documentos
            </Button>
            <Button variant="secondary" onClick={() => onNavigate("Métricas")}>
              Ver métricas
            </Button>
          </div>
        </>
      ) : null}
      <section className="content-panel" aria-labelledby="summary-chatbots-title">
        <h2 id="summary-chatbots-title">Chatbots</h2>
        <ul className="chatbot-summary-list">
          {chatbots.map((chatbot) => (
            <li key={chatbot.id}>
              <span>{chatbot.name}</span>
              <span>
                {chatbot.configured_llm_model.provider} ·{" "}
                {chatbot.configured_llm_model.model}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
