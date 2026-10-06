"use client";

import { useEffect, useRef, useState } from "react";
import type { MetricsPoint, MetricsSummary } from "@/types/api";

const dateFormat = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  timeZone: "UTC",
});
const fullDateFormat = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});
const numberFormat = new Intl.NumberFormat("es-EC", { maximumFractionDigits: 1 });
export const formatMetricTime = (value: number | null) =>
  value === null ? "No disponible" : `${numberFormat.format(value)} ms`;

function Timeline({
  points,
  kind,
}: Readonly<{ points: MetricsPoint[]; kind: "queries" | "time" }>) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [canvasWidth, setCanvasWidth] = useState(720);
  useEffect(() => {
    if (!svgRef.current) return;
    const observer = new ResizeObserver(([entry]) => {
      setCanvasWidth(Math.max(280, Math.round(entry.contentRect.width)));
    });
    observer.observe(svgRef.current);
    return () => observer.disconnect();
  }, []);
  const values = points.map((p) =>
    kind === "queries" ? p.total_queries : p.average_response_time_ms,
  );
  const maximum = Math.max(1, ...values.filter((v): v is number => v !== null));
  const left = 64,
    top = 16,
    width = canvasWidth - left - 24,
    height = 160;
  const x = (i: number) => left + (width * (i + 0.5)) / points.length;
  const y = (value: number) => top + height * (1 - value / maximum);
  const ticks = [
    ...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1]),
  ];
  const path = values
    .map((value, index) =>
      value === null
        ? ""
        : `${index === 0 || values[index - 1] === null ? "M" : "L"}${x(index)},${y(value)}`,
    )
    .join(" ");
  return (
    <svg
      className="metrics-timeline"
      ref={svgRef}
      viewBox={`0 0 ${canvasWidth} 215`}
      role="img"
      aria-label={
        kind === "queries"
          ? "Consultas por periodo; valores disponibles en la tabla de datos"
          : "Tiempo medio por periodo en milisegundos; valores disponibles en la tabla de datos"
      }
    >
      {[0, 0.5, 1].map((ratio) => (
        <g key={ratio}>
          <line
            className="metrics-gridline"
            x1={left}
            x2={left + width}
            y1={top + height * (1 - ratio)}
            y2={top + height * (1 - ratio)}
          />
          <text x={left - 10} y={top + height * (1 - ratio) + 4} textAnchor="end">
            {numberFormat.format(maximum * ratio)}
          </text>
        </g>
      ))}
      {kind === "queries" ? (
        values.map((value, index) => (
          <rect
            key={points[index].period_start}
            className="metrics-bar"
            x={x(index) - (width / points.length) * 0.33}
            y={y(value ?? 0)}
            width={(width / points.length) * 0.66}
            height={(height * (value ?? 0)) / maximum}
          >
            <title>
              {fullDateFormat.format(new Date(points[index].period_start))}: {value}{" "}
              consultas
            </title>
          </rect>
        ))
      ) : (
        <>
          <path className="metrics-line" d={path} />
          {values.map((value, index) =>
            value === null ? null : (
              <circle
                key={points[index].period_start}
                className="metrics-point"
                cx={x(index)}
                cy={y(value)}
                r={3}
              >
                <title>
                  {fullDateFormat.format(new Date(points[index].period_start))}:{" "}
                  {formatMetricTime(value)}
                </title>
              </circle>
            ),
          )}
        </>
      )}
      {ticks.map((index) => (
        <text key={index} x={x(index)} y={202} textAnchor="middle">
          {dateFormat.format(new Date(points[index].period_start))}
        </text>
      ))}
    </svg>
  );
}

export function MetricsCharts({ metrics }: Readonly<{ metrics: MetricsSummary }>) {
  const points = metrics.series ?? [];
  const grouping = { day: "Día", week: "Semana", month: "Mes" }[
    metrics.interval ?? "day"
  ];
  const states = [
    { key: "completed", label: "Completadas", value: metrics.completed_queries },
    { key: "failed", label: "Fallidas", value: metrics.failed_queries },
    { key: "processing", label: "En proceso", value: metrics.processing_queries },
  ];
  return (
    <>
      <div className="metrics-charts-grid">
        <section
          className="content-panel metrics-chart"
          aria-labelledby="query-trend-title"
        >
          <h3 id="query-trend-title">Consultas por periodo</h3>
          <p className="chart-caption">
            {grouping} · Fechas en UTC · {metrics.total_queries.toLocaleString("es-EC")}{" "}
            consultas
          </p>
          {points.length ? (
            <Timeline points={points} kind="queries" />
          ) : (
            <p className="muted-copy">
              No hay consultas para los filtros seleccionados.
            </p>
          )}
        </section>
        <section
          className="content-panel metrics-chart"
          aria-labelledby="response-trend-title"
        >
          <h3 id="response-trend-title">Tiempo medio de respuesta</h3>
          <p className="chart-caption">
            Milisegundos · Solo consultas completadas con tiempo medido
          </p>
          {points.some((p) => p.average_response_time_ms !== null) ? (
            <Timeline points={points} kind="time" />
          ) : (
            <p className="muted-copy">
              No hay tiempos medidos para los filtros seleccionados.
            </p>
          )}
        </section>
        <section
          className="content-panel metrics-chart metrics-outcomes"
          aria-labelledby="outcome-title"
        >
          <h3 id="outcome-title">Estados de las consultas</h3>
          <p className="chart-caption">
            Distribución dentro de los filtros seleccionados
          </p>
          {metrics.total_queries > 0 ? (
            <div className="result-bar" aria-hidden="true">
              {states.map((s) => (
                <span
                  key={s.key}
                  data-status={s.key}
                  style={{ width: `${(s.value / metrics.total_queries) * 100}%` }}
                />
              ))}
            </div>
          ) : null}
          <dl className="status-list">
            {states.map((s) => (
              <div key={s.key}>
                <dt>
                  <span className="status-dot" data-status={s.key} aria-hidden="true" />
                  {s.label}
                </dt>
                <dd>
                  {s.value.toLocaleString("es-EC")}{" "}
                  <span className="muted-copy">
                    (
                    {metrics.total_queries
                      ? numberFormat.format((s.value / metrics.total_queries) * 100)
                      : "0"}{" "}
                    %)
                  </span>
                </dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
      {points.length ? (
        <details className="metrics-data content-panel">
          <summary>Ver tabla de datos ({points.length} periodos)</summary>
          <div
            className="metrics-table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Datos de los gráficos"
          >
            <table>
              <caption>Consultas y tiempos por {grouping.toLowerCase()} · UTC</caption>
              <thead>
                <tr>
                  <th scope="col">Inicio del periodo</th>
                  <th scope="col">Consultas</th>
                  <th scope="col">Completadas</th>
                  <th scope="col">Fallidas</th>
                  <th scope="col">En proceso</th>
                  <th scope="col">Tiempo medio</th>
                </tr>
              </thead>
              <tbody>
                {points.map((p) => (
                  <tr key={p.period_start}>
                    <th scope="row">
                      {fullDateFormat.format(new Date(p.period_start))}
                    </th>
                    <td>{p.total_queries}</td>
                    <td>{p.completed_queries}</td>
                    <td>{p.failed_queries}</td>
                    <td>{p.processing_queries}</td>
                    <td>{formatMetricTime(p.average_response_time_ms)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </>
  );
}
