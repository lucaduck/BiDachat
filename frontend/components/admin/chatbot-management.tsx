"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Alert, EmptyState, LoadingState } from "@/components/ui/status";
import { deleteChatbot, listLlmModels } from "@/services/chatbot-service";
import { getWidgetSettings, integrationScript } from "@/services/widget-settings";
import type { Chatbot, LlmModel } from "@/types/api";
import { ChatbotWizard } from "./chatbot-wizard";
import { workspaceUrl, type WorkspaceRoute } from "@/lib/navigation";
import type { Navigate } from "@/lib/use-workspace-navigation";
import { ChatbotActivity, useChatbotActivity } from "./chatbot-activity";
import { contrastTextColor } from "@/services/widget-settings";

type ChatbotManagementProps = {
  chatbots: Chatbot[];
  route: WorkspaceRoute;
  navigate: Navigate;
  onDirtyChange: (dirty: boolean) => void;
  onApiError: (error: unknown) => void;
  onChanged: (message: string, saved?: Chatbot) => void;
  token: string;
};

export function ChatbotManagement({
  chatbots,
  route,
  navigate,
  onDirtyChange,
  onApiError,
  onChanged,
  token,
}: Readonly<ChatbotManagementProps>) {
  const [models, setModels] = useState<LlmModel[] | null>(null);
  const [modelError, setModelError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const editingId = route.editId;
  const isCreating = route.creating;
  const selected = chatbots.find((item) => item.id === editingId);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const publicOrigin = typeof window === "undefined" ? "" : window.location.origin;
  const activity = useChatbotActivity(
    chatbots,
    token,
    onApiError,
    !editingId && !isCreating,
  );

  useEffect(() => {
    let active = true;
    listLlmModels(token)
      .then((availableModels) => {
        if (active) {
          setModels(availableModels);
          setModelError(false);
        }
      })
      .catch((requestError) => {
        if (active) {
          onApiError(requestError);
          setModelError(true);
        }
      });
    return () => {
      active = false;
    };
  }, [onApiError, reloadKey, token]);

  function startCreate() {
    navigate({ view: "Chatbots", creating: true, step: 0 });
    setConfirmDeleteId(null);
    setError(null);
  }

  function startEdit(chatbot: Chatbot) {
    navigate({ view: "Chatbots", editId: chatbot.id, step: 0 });
    setConfirmDeleteId(null);
    setError(null);
  }

  async function removeChatbot(chatbotId: string) {
    setIsSaving(true);
    setError(null);
    try {
      await deleteChatbot(token, chatbotId);
      setConfirmDeleteId(null);
      onChanged("Chatbot eliminado.");
    } catch (requestError) {
      onApiError(requestError);
      setError("No se pudo eliminar el chatbot. Inténtalo nuevamente.");
    } finally {
      setIsSaving(false);
    }
  }

  async function copyScript(chatbotId: string) {
    try {
      await navigator.clipboard.writeText(
        integrationScript(
          publicOrigin,
          chatbotId,
          getWidgetSettings(
            chatbots.find((item) => item.id === chatbotId)?.widget_settings,
          ),
          chatbots.find((item) => item.id === chatbotId)?.name,
        ),
      );
      setCopiedId(chatbotId);
    } catch {
      setError(
        "No se pudo copiar el script. Selecciona el texto y cópialo manualmente.",
      );
    }
  }

  return (
    <section aria-label="Gestión de chatbots">
      {!editingId && !isCreating ? (
        <>
          <ChatbotActivity {...activity} chatbotCount={chatbots.length} />
          <div className="section-heading">
            <div>
              <h2>
                Asistentes configurados{" "}
                <span className="count-badge">{chatbots.length}</span>
              </h2>
              <p>Selecciona un chatbot para editarlo o probar su integración.</p>
            </div>
            <Button
              onClick={startCreate}
              disabled={models === null || models.length === 0}
            >
              <Icon name="plus" />
              Crear chatbot
            </Button>
          </div>
        </>
      ) : null}
      {modelError ? (
        <Alert tone="error">
          No se pudieron cargar los modelos.{" "}
          <button
            className="text-action"
            type="button"
            onClick={() => setReloadKey((key) => key + 1)}
          >
            Reintentar
          </button>
        </Alert>
      ) : null}
      {models === null && !modelError ? (
        <LoadingState label="Cargando modelos disponibles…" />
      ) : null}
      {models?.length === 0 ? (
        <Alert tone="warning">
          No hay modelos de lenguaje disponibles para crear chatbots.
        </Alert>
      ) : null}
      {error ? <Alert tone="error">{error}</Alert> : null}
      {(isCreating || (editingId && selected)) && models ? (
        <ChatbotWizard
          key={editingId ?? "new"}
          chatbot={selected}
          initialStep={route.step}
          onStepChange={(step) => navigate({ ...route, step }, { withinEditor: true })}
          onDirtyChange={onDirtyChange}
          onSaved={(saved, step) => {
            const stayed = navigate(
              { view: "Chatbots", editId: saved.id, step },
              {
                replace: true,
                withinEditor: true,
                ifCurrentEditor: editingId ?? "new",
              },
            );
            if (stayed) onDirtyChange(false);
            onChanged("Configuración guardada.", saved);
          }}
          models={models}
          token={token}
          onApiError={onApiError}
          onClose={(changed) => {
            if (navigate({ view: "Chatbots" }) && changed)
              onChanged("Configuración del chatbot guardada.");
          }}
        />
      ) : null}
      {editingId && !selected ? (
        <EmptyState
          title="Este chatbot no está disponible"
          description="Puede haber sido eliminado. Vuelve al listado para elegir otro asistente."
          action={
            <Button variant="secondary" onClick={() => navigate({ view: "Chatbots" })}>
              Volver a Chatbots
            </Button>
          }
        />
      ) : null}
      {chatbots.length === 0 && !isCreating && !editingId ? (
        <EmptyState
          title="No hay chatbots configurados"
          description="Crea el primero para asociar documentos y consultar métricas."
          action={
            models?.length ? (
              <Button onClick={startCreate}>Crear chatbot</Button>
            ) : undefined
          }
        />
      ) : null}
      {chatbots.length > 0 && !editingId && !isCreating ? (
        <ul className="chatbot-list">
          {chatbots.map((chatbot) => {
            const appearance = getWidgetSettings(chatbot.widget_settings);
            const metrics = activity.records?.[chatbot.id];
            return (
              <li className="chatbot-row" key={chatbot.id}>
                <div className="chatbot-card-content">
                  <div className="chatbot-card-heading">
                    <span
                      className="chatbot-avatar"
                      style={{
                        backgroundColor: appearance.primaryColor,
                        color: contrastTextColor(appearance.primaryColor),
                      }}
                    >
                      <Icon
                        name={appearance.icon === "chat" ? "message" : appearance.icon}
                      />
                    </span>
                    <div>
                      <h3>{chatbot.name}</h3>
                      <span className="configuration-badge">Configurado</span>
                    </div>
                  </div>
                  <p className="chatbot-description">
                    {chatbot.description || "Sin descripción"}
                  </p>
                  <small className="model-label">
                    {chatbot.configured_llm_model.provider} ·{" "}
                    {chatbot.configured_llm_model.model}
                  </small>
                  <dl className="chatbot-card-activity">
                    <div>
                      <dt>Consultas</dt>
                      <dd>{metrics?.total_queries.toLocaleString("es-EC") ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Completadas</dt>
                      <dd>
                        {metrics?.completed_queries.toLocaleString("es-EC") ?? "—"}
                      </dd>
                    </div>
                  </dl>
                  <details className="integration-snippet">
                    <summary>Código de integración</summary>
                    <div className="snippet-content">
                      <label htmlFor={`snippet-${chatbot.id}`}>
                        Script de integración
                      </label>
                      <small>
                        Tras editar la apariencia, reemplaza este script en los
                        dashboards integrados.
                      </small>
                      <textarea
                        id={`snippet-${chatbot.id}`}
                        readOnly
                        rows={3}
                        value={integrationScript(
                          publicOrigin,
                          chatbot.id,
                          getWidgetSettings(chatbot.widget_settings),
                          chatbot.name,
                        )}
                        onFocus={(event) => event.currentTarget.select()}
                      />
                      <button
                        className="copy-script"
                        type="button"
                        onClick={() => void copyScript(chatbot.id)}
                      >
                        <Icon name={copiedId === chatbot.id ? "check" : "copy"} />
                        <span>
                          {copiedId === chatbot.id ? "Script copiado" : "Copiar script"}
                        </span>
                      </button>
                    </div>
                  </details>
                </div>
                <div className="row-actions">
                  <a
                    className="button button-primary"
                    href={workspaceUrl({ view: "Chatbots", editId: chatbot.id })}
                    onClick={(event) => {
                      if (
                        !event.metaKey &&
                        !event.ctrlKey &&
                        !event.shiftKey &&
                        !event.altKey
                      ) {
                        event.preventDefault();
                        startEdit(chatbot);
                      }
                    }}
                  >
                    <Icon name="edit" />
                    Editar
                  </a>
                  <a
                    className="button button-secondary"
                    href={`${publicOrigin}/preview?${new URLSearchParams({ chatbot_id: chatbot.id, color: getWidgetSettings(chatbot.widget_settings).primaryColor, icon: getWidgetSettings(chatbot.widget_settings).icon, title: chatbot.name, welcome: getWidgetSettings(chatbot.widget_settings).welcomeMessage }).toString()}`}
                  >
                    <Icon name="arrow" />
                    <span>
                      Probar
                      <span className="sr-only"> {chatbot.name}</span>
                    </span>
                  </a>
                  <Button
                    variant="quiet"
                    type="button"
                    disabled={isSaving}
                    onClick={() => setConfirmDeleteId(chatbot.id)}
                  >
                    <Icon name="trash" />
                    Eliminar
                  </Button>
                </div>
                {confirmDeleteId === chatbot.id ? (
                  <div className="delete-confirmation">
                    <p>
                      ¿Eliminar «{chatbot.name}» y sus métricas? Las fuentes compartidas
                      se conservarán.
                    </p>
                    <Button
                      variant="danger"
                      type="button"
                      isLoading={isSaving}
                      onClick={() => void removeChatbot(chatbot.id)}
                    >
                      Confirmar eliminación
                    </Button>
                    <Button
                      variant="secondary"
                      type="button"
                      disabled={isSaving}
                      onClick={() => setConfirmDeleteId(null)}
                    >
                      Cancelar
                    </Button>
                  </div>
                ) : null}
              </li>
            );
          })}
          <li className="chatbot-create-card">
            <button type="button" onClick={startCreate} disabled={!models?.length}>
              <span className="create-card-symbol">
                <Icon name="plus" />
              </span>
              <strong>Crear nuevo chatbot</strong>
              <span>
                Configura un asistente y conéctalo con tus fuentes de conocimiento.
              </span>
            </button>
          </li>
        </ul>
      ) : null}
    </section>
  );
}
