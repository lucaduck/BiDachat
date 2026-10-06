import type { ReactNode } from "react";

type AlertTone = "error" | "info" | "success" | "warning";
export function Alert({
  children,
  tone = "info",
}: Readonly<{ children: ReactNode; tone?: AlertTone }>) {
  return (
    <div className={`alert alert-${tone}`} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
export function EmptyState({
  action,
  description,
  title,
}: Readonly<{ action?: ReactNode; description: string; title: string }>) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>{description}</p>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
export function LoadingState({
  label = "Cargando información…",
}: Readonly<{ label?: string }>) {
  return (
    <div className="loading-state" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}
