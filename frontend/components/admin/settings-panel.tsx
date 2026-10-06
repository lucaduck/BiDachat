"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { SelectField } from "@/components/ui/field";
import { Icon } from "@/components/ui/icon";
import { Alert, LoadingState } from "@/components/ui/status";
import { listLlmModels } from "@/services/chatbot-service";
import { getSystemSettings, type SystemSettings } from "@/services/settings-service";
import { getWidgetSettings, integrationScript } from "@/services/widget-settings";
import type { Chatbot, LlmModel } from "@/types/api";

type Props = {
  token: string;
  chatbots: Chatbot[];
  onApiError: (error: unknown) => void;
  onManageChatbots: () => void;
};

export function SettingsPanel({
  token,
  chatbots,
  onApiError,
  onManageChatbots,
}: Readonly<Props>) {
  const [configuration, setConfiguration] = useState<SystemSettings | null>(null);
  const [models, setModels] = useState<LlmModel[]>([]);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedId, setSelectedId] = useState(chatbots[0]?.id ?? "");
  const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");

  useEffect(() => {
    let active = true;
    Promise.all([getSystemSettings(token), listLlmModels(token)])
      .then(([settings, availableModels]) => {
        if (!active) return;
        setConfiguration(settings);
        setModels(availableModels);
      })
      .catch((requestError) => {
        if (!active) return;
        onApiError(requestError);
        setError(true);
      });
    return () => {
      active = false;
    };
  }, [token, onApiError, reloadKey]);

  const selected = chatbots.find((chatbot) => chatbot.id === selectedId);
  const settings = selected ? getWidgetSettings(selected.widget_settings) : null;
  const origin = typeof window === "undefined" ? "" : window.location.origin;
  const snippet =
    selected && settings && origin
      ? integrationScript(origin, selected.id, settings, selected.name)
      : "";
  const previewParameters =
    selected && settings
      ? new URLSearchParams({
          chatbot_id: selected.id,
          title: selected.name,
          color: settings.primaryColor,
          icon: settings.icon,
          welcome: settings.welcomeMessage,
        })
      : null;

  if (error)
    return (
      <Alert tone="error">
        No se pudo cargar la configuración.{" "}
        <button
          className="text-action"
          type="button"
          onClick={() => {
            setError(false);
            setConfiguration(null);
            setReloadKey((value) => value + 1);
          }}
        >
          Reintentar
        </button>
      </Alert>
    );
  if (!configuration) return <LoadingState label="Cargando configuración…" />;

  return (
    <div className="settings-panel">
      <p className="settings-help">
        Estos ajustes reflejan la configuración actual del servidor. Las credenciales y
        los parámetros del despliegue los administra el responsable técnico.
      </p>
      <section className="settings-section" aria-labelledby="settings-models">
        <div className="section-heading">
          <div>
            <h2 id="settings-models">Proveedores y modelos de lenguaje</h2>
            <p>El modelo de respuesta se elige al configurar cada chatbot.</p>
          </div>
          <Button variant="secondary" onClick={onManageChatbots}>
            Gestionar chatbots
          </Button>
        </div>
        <dl className="settings-values">
          <div>
            <dt>Credencial de Gemini</dt>
            <dd>
              {configuration.gemini_configured
                ? "Configurada"
                : "Pendiente de configurar"}
            </dd>
          </div>
          <div>
            <dt>Credencial de OpenAI</dt>
            <dd>
              {configuration.openai_configured
                ? "Configurada"
                : "Pendiente de configurar"}
            </dd>
          </div>
          <div>
            <dt>Credencial de OpenRouter</dt>
            <dd>
              {configuration.openrouter_configured
                ? "Configurada"
                : "Pendiente de configurar"}
            </dd>
          </div>
        </dl>
        <p className="field-hint">
          Una credencial configurada no confirma la disponibilidad del proveedor.
        </p>
        <h3>Modelos registrados</h3>
        {models.length ? (
          <ul className="settings-models">
            {models.map((model) => (
              <li key={model.id}>
                <span>{model.provider}</span>
                <strong>{model.model}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p>No hay modelos registrados.</p>
        )}
      </section>

      <section className="settings-section" aria-labelledby="settings-widget">
        <div className="settings-widget-heading">
          <span className="settings-widget-icon">
            <Icon name="code" />
          </span>
          <div>
            <h2 id="settings-widget">Widget y seguridad</h2>
            <p>
              Inserta el chatbot en un sitio externo y revisa sus orígenes autorizados.
            </p>
          </div>
        </div>
        {chatbots.length ? (
          <>
            <div className="settings-widget-select">
              <SelectField
                id="settings-chatbot"
                label="Chatbot para integrar"
                value={selectedId}
                onChange={(event) => {
                  setSelectedId(event.target.value);
                  setCopyStatus("idle");
                }}
              >
                {chatbots.map((chatbot) => (
                  <option key={chatbot.id} value={chatbot.id}>
                    {chatbot.name}
                  </option>
                ))}
              </SelectField>
              {previewParameters ? (
                <a
                  className="button button-secondary"
                  href={`/preview?${previewParameters}`}
                >
                  <Icon name="eye" /> Vista previa
                </a>
              ) : null}
            </div>
            {selected ? (
              <p className="settings-selected-chatbot" aria-live="polite">
                Se integrará: <strong>{selected.name}</strong>
              </p>
            ) : null}
            <div className="settings-code-heading">
              <label htmlFor="settings-snippet">Código de integración</label>
              <Button
                disabled={!snippet}
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(snippet);
                    setCopyStatus("success");
                  } catch {
                    setCopyStatus("error");
                  }
                }}
              >
                <Icon name="copy" />
                {copyStatus === "success" ? "Copiado" : "Copiar código"}
              </Button>
            </div>
            <textarea
              id="settings-snippet"
              className="input settings-snippet"
              value={snippet}
              readOnly
              rows={5}
              onFocus={(event) => event.currentTarget.select()}
            />
            {copyStatus === "success" ? (
              <p role="status">Código de integración copiado.</p>
            ) : null}
            {copyStatus === "error" ? (
              <Alert tone="error">
                No se pudo copiar. Selecciona el código y cópialo manualmente.
              </Alert>
            ) : null}
            <p className="field-hint">
              Si cambias la apariencia del chatbot, reemplaza el script en los
              dashboards integrados.
            </p>
          </>
        ) : (
          <p>Crea un chatbot desde «Chatbots» para obtener su código de integración.</p>
        )}
        <div className="settings-origins-heading">
          <div>
            <h3>Orígenes externos autorizados</h3>
            <p>Sitios desde los que se permite usar el widget.</p>
          </div>
          <span>{configuration.widget_allowed_origins.length} autorizados</span>
        </div>
        {configuration.widget_allowed_origins.length ? (
          <ul className="settings-origins">
            {configuration.widget_allowed_origins.map((origin) => (
              <li key={origin}>{origin}</li>
            ))}
          </ul>
        ) : (
          <p>
            No hay orígenes externos autorizados. Puedes probar el widget desde esta
            aplicación.
          </p>
        )}
      </section>

      <section className="settings-section" aria-labelledby="settings-knowledge">
        <h2 id="settings-knowledge">Conocimiento y sesión</h2>
        {configuration.embedding_provider === "gemini" &&
        !configuration.gemini_configured ? (
          <Alert tone="warning">
            Falta configurar la credencial de Gemini para generar los embeddings de los
            documentos.
          </Alert>
        ) : null}
        <dl className="settings-values">
          <div>
            <dt>Almacenamiento vectorial</dt>
            <dd>PostgreSQL + pgvector</dd>
          </div>
          <div>
            <dt>Proveedor de embeddings</dt>
            <dd>
              {configuration.embedding_provider === "ollama"
                ? "Ollama local"
                : "Gemini"}
            </dd>
          </div>
          <div>
            <dt>Modelo de embeddings</dt>
            <dd>{configuration.embedding_model}</dd>
          </div>
          <div>
            <dt>Dimensiones</dt>
            <dd>{configuration.embedding_dimensions}</dd>
          </div>
          <div>
            <dt>Tamaño máximo por documento</dt>
            <dd>{configuration.document_max_size_bytes / (1024 * 1024)} MB</dd>
          </div>
          <div>
            <dt>Duración máxima de la sesión</dt>
            <dd>{configuration.session_ttl_minutes} minutos</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
