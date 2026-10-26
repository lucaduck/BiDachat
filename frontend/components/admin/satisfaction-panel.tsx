"use client";

import { useEffect, useState } from "react";
import { Alert, LoadingState } from "@/components/ui/status";
import { getSurveyComments } from "@/services/satisfaction-service";
import type { SatisfactionMetrics, SurveyCommentsPage } from "@/types/api";

type Props = {
  metrics: SatisfactionMetrics;
  chatbotId: string;
  token: string;
  startedAt?: string;
  endedAt?: string;
  onApiError: (error: unknown) => void;
};

const percent = (value: number | null) =>
  value === null
    ? "Sin datos"
    : `${(value * 100).toLocaleString("es-EC", { maximumFractionDigits: 1 })} %`;

export function SatisfactionPanel({
  metrics,
  chatbotId,
  token,
  startedAt,
  endedAt,
  onApiError,
}: Readonly<Props>) {
  const scope = `${chatbotId}:${startedAt ?? "all"}:${endedAt ?? "all"}`;
  const [pagination, setPagination] = useState({ scope, offset: 0 });
  const offset = pagination.scope === scope ? pagination.offset : 0;
  const queryKey = `${scope}:${offset}`;
  const [loaded, setLoaded] = useState<{
    key: string;
    data: SurveyCommentsPage;
  } | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const comments = loaded?.key === queryKey ? loaded.data : null;
  const error = errorKey === queryKey;

  useEffect(() => {
    let active = true;
    getSurveyComments(token, chatbotId, startedAt, endedAt, offset)
      .then((result) => {
        if (active) {
          setLoaded({ key: queryKey, data: result });
          setErrorKey(null);
        }
      })
      .catch((requestError) => {
        if (active) {
          onApiError(requestError);
          setErrorKey(queryKey);
        }
      });
    return () => {
      active = false;
    };
  }, [chatbotId, token, startedAt, endedAt, offset, queryKey, onApiError, retry]);

  const maximum = Math.max(1, ...Object.values(metrics.scores));
  return (
    <section className="satisfaction-section" aria-labelledby="satisfaction-heading">
      <div className="section-heading">
        <div>
          <h2 id="satisfaction-heading">Satisfacción de visitantes</h2>
          <p>
            Percepción declarada al finalizar una conversación; no mide exactitud
            factual.
          </p>
        </div>
      </div>
      <p className="metrics-filter-hint">
        Se aplican chatbot, periodo y agrupación UTC. El filtro «Estado» solo
        corresponde a las consultas. Una respuesta tardía actualiza el periodo en que se
        ofreció la encuesta.
      </p>
      <dl className="metric-grid">
        <div className="metric-card">
          <dt>Encuestas ofrecidas</dt>
          <dd>{metrics.offers}</dd>
        </div>
        <div className="metric-card">
          <dt>Respuestas</dt>
          <dd>{metrics.responses}</dd>
        </div>
        <div className="metric-card">
          <dt>Participación</dt>
          <dd>{percent(metrics.participation_rate)}</dd>
          <small>
            {metrics.responses} de {metrics.offers} ofertas
          </small>
        </div>
        <div className="metric-card">
          <dt>CSAT (4 o 5)</dt>
          <dd>{percent(metrics.csat_rate)}</dd>
          <small>
            {metrics.satisfied} de {metrics.responses} respuestas
          </small>
        </div>
        <div className="metric-card">
          <dt>Claridad media</dt>
          <dd>
            {metrics.average_clarity === null
              ? "Sin datos"
              : `${metrics.average_clarity.toFixed(1)} / 5`}
          </dd>
          <small>{metrics.clarity_count} respuestas</small>
        </div>
        <div className="metric-card">
          <dt>Consulta resuelta</dt>
          <dd>{percent(metrics.resolution_rate)}</dd>
          <small>
            {metrics.resolved} de {metrics.resolution_count} respuestas
          </small>
        </div>
      </dl>
      <div className="metrics-charts-grid satisfaction-charts">
        <figure className="metric-chart">
          <h3>Distribución de satisfacción</h3>
          <div
            className="satisfaction-bars"
            role="img"
            aria-label="Distribución de puntuaciones de satisfacción"
          >
            {[1, 2, 3, 4, 5].map((score) => (
              <div key={score} className="satisfaction-bar">
                <span>{score}</span>
                <span className="satisfaction-bar-track">
                  <span
                    style={{ width: `${(metrics.scores[score] / maximum) * 100}%` }}
                  />
                </span>
                <strong>{metrics.scores[score]}</strong>
              </div>
            ))}
          </div>
        </figure>
        <figure className="metric-chart">
          <h3>Evolución de respuestas</h3>
          <div
            className="satisfaction-timeline"
            role="img"
            aria-label="Respuestas por periodo"
          >
            {metrics.series.length ? (
              metrics.series.map((point) => (
                <div
                  key={point.period_start}
                  title={`${point.period_start.slice(0, 10)}: ${point.responses} respuestas de ${point.offers} ofertas`}
                >
                  <span
                    style={{
                      height: `${Math.max(2, (point.responses / Math.max(1, ...metrics.series.map((item) => item.responses))) * 100)}%`,
                    }}
                  />
                </div>
              ))
            ) : (
              <p>Sin datos para este periodo.</p>
            )}
          </div>
        </figure>
      </div>
      <details className="metrics-data">
        <summary>Ver datos por periodo</summary>
        <div className="metrics-table-scroll">
          <table>
            <caption>Ofertas y respuestas agrupadas por fecha de oferta en UTC</caption>
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Ofertas</th>
                <th>Respuestas</th>
                <th>CSAT (4–5)</th>
                <th>Claridad respondida</th>
                <th>Resuelta</th>
              </tr>
            </thead>
            <tbody>
              {metrics.series.map((point) => (
                <tr key={point.period_start}>
                  <th scope="row">{point.period_start.slice(0, 10)}</th>
                  <td>{point.offers}</td>
                  <td>{point.responses}</td>
                  <td>{point.satisfied}</td>
                  <td>{point.clarity_count}</td>
                  <td>
                    {point.resolved} / {point.resolution_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <section aria-label="Comentarios de visitantes" className="survey-comments">
        <h3>Comentarios voluntarios</h3>
        {error ? (
          <Alert tone="error">
            No se pudieron cargar los comentarios.{" "}
            <button
              type="button"
              onClick={() => {
                setErrorKey(null);
                setLoaded(null);
                setRetry((value) => value + 1);
              }}
            >
              Reintentar
            </button>
          </Alert>
        ) : null}
        {!comments && !error ? <LoadingState label="Cargando comentarios…" /> : null}
        {comments && !error ? (
          <>
            {comments.items.length ? (
              <ul>
                {comments.items.map((item, index) => (
                  <li key={`${item.submitted_at}-${index}`}>
                    <time dateTime={item.submitted_at}>
                      {item.submitted_at.slice(0, 10)}
                    </time>
                    <p>{item.comment}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Sin comentarios en este periodo.</p>
            )}
            <div className="survey-pagination">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() =>
                  setPagination({ scope, offset: Math.max(0, offset - 10) })
                }
              >
                Anterior
              </button>
              <span>
                {comments.total
                  ? `${offset + 1}–${Math.min(offset + 10, comments.total)} de ${comments.total}`
                  : "0 comentarios"}
              </span>
              <button
                type="button"
                disabled={offset + 10 >= comments.total}
                onClick={() => setPagination({ scope, offset: offset + 10 })}
              >
                Siguiente
              </button>
            </div>
          </>
        ) : null}
      </section>
    </section>
  );
}
