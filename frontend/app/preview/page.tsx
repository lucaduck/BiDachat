"use client";
import "./preview.css";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Brand } from "@/components/ui/brand";
import { Alert } from "@/components/ui/status";
import { workspaceUrl, UUID_PATTERN } from "@/lib/navigation";
import { isHexColor, isWidgetIcon } from "@/services/widget-settings";

function ChatbotPreview() {
  const parameters = useSearchParams();
  const chatbotId = parameters.get("chatbot_id") ?? "";
  const color = parameters.get("color") ?? "";
  const icon = parameters.get("icon") ?? "";
  const welcome = parameters.get("welcome") ?? "";
  const title = parameters.get("title") ?? "";
  const returnStep = parameters.get("editor_step") === "4" ? "4" : "0";
  const container = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState(false);
  const validId = UUID_PATTERN.test(chatbotId);
  const editorUrl = workspaceUrl({
    view: "Chatbots",
    editId: validId ? chatbotId : undefined,
    step: Number(returnStep),
  });

  useEffect(() => {
    if (!validId) return;
    const previousWidgets = new Set(document.querySelectorAll("bidachat-widget"));
    let mountedWidget: Element | undefined;
    let disposed = false;
    const script = document.createElement("script");
    script.src = "/bidachat-widget.js";
    script.dataset.apiBase = `${window.location.origin}/api/v1`;
    script.dataset.chatbotId = chatbotId;
    script.dataset.theme =
      localStorage.getItem("bidachat-theme") === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = script.dataset.theme;
    if (isHexColor(color)) script.dataset.primaryColor = color;
    if (isWidgetIcon(icon)) script.dataset.icon = icon;
    if (welcome && welcome.length <= 300) script.dataset.welcomeMessage = welcome;
    if (title && title.length <= 200) script.dataset.title = title;
    script.onerror = () => setLoadError(true);
    script.onload = () => {
      mountedWidget = Array.from(document.querySelectorAll("bidachat-widget")).find(
        (widget) => !previousWidgets.has(widget),
      );
      if (disposed) mountedWidget?.remove();
    };
    container.current?.appendChild(script);
    return () => {
      disposed = true;
      script.remove();
      mountedWidget?.remove();
    };
  }, [chatbotId, color, icon, title, welcome, validId]);

  return (
    <main className="preview-page">
      <Brand />
      <section className="preview-content">
        <div className="preview-intro">
          <div>
            <h1>Prueba de integración</h1>
            <p>
              Abre el asistente para conversar, adjuntar una imagen o capturar la
              pantalla. Las consultas se registran en sus métricas.
            </p>
          </div>
          <Link className="button button-secondary" href={editorUrl}>
            Volver al editor
          </Link>
        </div>
        {!validId ? (
          <Alert tone="error">
            El identificador del chatbot no es válido. Abre esta página desde el botón
            Probar de tu chatbot.
          </Alert>
        ) : null}
        {loadError ? (
          <Alert tone="error">
            No se pudo cargar el widget. Recarga esta página para intentarlo nuevamente.
          </Alert>
        ) : null}
        <div className="preview-dashboard" aria-label="Dashboard de demostración">
          <div className="preview-dashboard-heading">
            <div>
              <h2>Tablero de análisis</h2>
              <p>Datos de demostración para probar preguntas y capturas.</p>
            </div>
            <span>Trimestre actual</span>
          </div>
          <div className="preview-kpis">
            <div>
              <span>Rendimiento operativo</span>
              <strong>89,4 %</strong>
              <small>+3,4 % respecto al periodo anterior</small>
            </div>
            <div>
              <span>Ejecución trimestral</span>
              <strong>74,2 %</strong>
              <small>−8,2 % respecto al periodo anterior</small>
            </div>
            <div>
              <span>Cumplimiento de metas</span>
              <strong>92,0 %</strong>
              <small>Meta institucional</small>
            </div>
          </div>
          <div className="preview-analysis">
            <div className="preview-analysis-heading">
              <div>
                <h3>Ejecución por semana</h3>
                <p>Comparación visual para probar el análisis de capturas</p>
              </div>
              <span>Programado / real</span>
            </div>
            <div
              className="preview-chart"
              role="img"
              aria-label="La ejecución disminuye en la semana cinco y se recupera en las semanas siguientes"
            >
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="preview-chart-labels" aria-hidden="true">
              <span>S1</span>
              <span>S2</span>
              <span>S3</span>
              <span>S4</span>
              <span>S5</span>
              <span>S6</span>
              <span>S7</span>
            </div>
          </div>
        </div>
      </section>
      <div ref={container} />
    </main>
  );
}

export default function PreviewPage() {
  return (
    <Suspense
      fallback={<main className="preview-page">Cargando prueba de integración…</main>}
    >
      <ChatbotPreview />
    </Suspense>
  );
}
