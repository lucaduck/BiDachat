import type { MetricsSummary } from "@/types/api";
export function UsageCharts({
  records,
  completed,
  failed,
  processing,
}: Readonly<{
  records: { id: string; name: string; metrics: MetricsSummary }[];
  completed: number;
  failed: number;
  processing: number;
}>) {
  const maximum = Math.max(1, ...records.map((r) => r.metrics.total_queries));
  const total = completed + failed + processing;
  const states = [
    { key: "completed", label: "Completadas", value: completed },
    { key: "failed", label: "Fallidas", value: failed },
    { key: "processing", label: "En proceso", value: processing },
  ];
  return (
    <div className="chart-grid">
      <section className="content-panel" aria-labelledby="usage-chart-title">
        <h2 id="usage-chart-title">Consultas por chatbot</h2>
        <p className="chart-caption">
          Últimos 30 días · Comparación del uso registrado
        </p>
        {total ? (
          <ul className="usage-bars">
            {records.map((r) => (
              <li key={r.id}>
                <span>{r.name}</span>
                <strong>{r.metrics.total_queries}</strong>
                <span className="bar-track" aria-hidden="true">
                  <span
                    className="bar-fill"
                    style={{ width: `${(r.metrics.total_queries / maximum) * 100}%` }}
                  />
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted-copy">Todavía no hay consultas en este periodo.</p>
        )}
      </section>
      <section className="content-panel" aria-labelledby="result-chart-title">
        <h2 id="result-chart-title">Resultado de las consultas</h2>
        <p className="chart-caption">Últimos 30 días · {total} consultas registradas</p>
        {total ? (
          <div className="result-bar" aria-hidden="true">
            {states.map((s) => (
              <span
                key={s.key}
                data-status={s.key}
                style={{ width: `${(s.value / total) * 100}%` }}
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
              <dd>{s.value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
