"use client";
import "./admin-panels.css";
import { useEffect, useState } from "react";
import { useSession } from "@/components/auth/session-provider";
import { AdminShell } from "@/components/layout/admin-shell";
import { Alert, LoadingState } from "@/components/ui/status";
import { useWorkspaceNavigation } from "@/lib/use-workspace-navigation";
import { listChatbots } from "@/services/chatbot-service";
import type { Chatbot } from "@/types/api";
import { DashboardSummary } from "./dashboard-summary";
import { ChatbotManagement } from "./chatbot-management";
import { DocumentManagement } from "./document-management";
import { MetricsPanel } from "./metrics-panel";
import { SettingsPanel } from "./settings-panel";
export function AdminWorkspace() {
  const { token, logout, handleApiError } = useSession();
  const { route, navigate, setDirty } = useWorkspaceNavigation();
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    if (!token) return;
    let active = true;
    listChatbots(token)
      .then((items) => {
        if (active) {
          setChatbots(items);
          setError(null);
          setLoaded(true);
        }
      })
      .catch((requestError) => {
        if (active) {
          handleApiError(requestError);
          setError("No se pudieron cargar los chatbots. Inténtalo nuevamente.");
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, handleApiError, reloadKey]);
  const common = { chatbots, token: token ?? "", onApiError: handleApiError };
  return (
    <AdminShell
      route={route}
      navigate={navigate}
      editorName={chatbots.find((bot) => bot.id === route.editId)?.name}
      onLogout={() => {
        if (navigate({ view: "Resumen" })) void logout();
      }}
    >
      {route.invalid ? (
        <Alert tone="warning">
          La dirección contiene parámetros no admitidos.{" "}
          <button
            className="text-action"
            onClick={() => navigate({ view: route.view }, { replace: true })}
          >
            Volver a una vista válida
          </button>
        </Alert>
      ) : null}
      {error ? (
        <Alert tone="error">
          {error}{" "}
          <button
            className="text-action"
            onClick={() => setReloadKey((key) => key + 1)}
          >
            Reintentar
          </button>
        </Alert>
      ) : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}
      {isLoading ? <LoadingState label="Cargando tu espacio de trabajo…" /> : null}
      {loaded && token && !route.invalid ? (
        <>
          {route.view === "Resumen" ? (
            <DashboardSummary {...common} onNavigate={(view) => navigate({ view })} />
          ) : null}
          {route.view === "Chatbots" ? (
            <ChatbotManagement
              {...common}
              route={route}
              navigate={navigate}
              onDirtyChange={setDirty}
              onChanged={(message, saved) => {
                setNotice(message);
                if (saved)
                  setChatbots((items) =>
                    items.some((bot) => bot.id === saved.id)
                      ? items.map((bot) => (bot.id === saved.id ? saved : bot))
                      : [...items, saved],
                  );
                setReloadKey((key) => key + 1);
              }}
            />
          ) : null}
          {route.view === "Documentos" ? (
            <DocumentManagement
              {...common}
              key={route.chatbotId ?? "documents"}
              initialChatbotId={route.chatbotId}
              onSelectionChange={(id) =>
                navigate({ view: "Documentos", chatbotId: id }, { replace: true })
              }
              onChanged={setNotice}
            />
          ) : null}
          {route.view === "Métricas" ? (
            <MetricsPanel
              {...common}
              key={`${route.chatbotId}-${route.period}-${route.interval}-${route.status}-${route.startDate}-${route.endDate}`}
              initialChatbotId={route.chatbotId}
              initialFilters={{
                period: route.period ?? "all",
                interval: route.interval ?? "day",
                status: route.status ?? "all",
                startDate: route.startDate ?? "",
                endDate: route.endDate ?? "",
              }}
              onFilterChange={(id, filters) =>
                navigate(
                  { view: "Métricas", chatbotId: id, ...filters },
                  { replace: true },
                )
              }
            />
          ) : null}
          {route.view === "Configuración" ? (
            <SettingsPanel
              {...common}
              onManageChatbots={() => navigate({ view: "Chatbots" })}
            />
          ) : null}
        </>
      ) : null}
    </AdminShell>
  );
}
