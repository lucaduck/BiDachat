"use client";
import { useEffect, useState } from "react";
import { integrationScript, type WidgetSettings } from "@/services/widget-settings";
export function WidgetPreview({
  name,
  settings,
}: Readonly<{ name: string; settings: WidgetSettings }>) {
  const [appearance, setAppearance] = useState({ name, settings });
  useEffect(() => {
    const timer = setTimeout(() => setAppearance({ name, settings }), 200);
    return () => clearTimeout(timer);
  }, [name, settings]);
  const [theme, setTheme] = useState("light");
  useEffect(() => {
    const sync = () => setTheme(document.documentElement.dataset.theme ?? "light");
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);
  const origin =
    typeof window === "undefined" ? "http://localhost:3000" : window.location.origin;
  const script = integrationScript(
    origin,
    "00000000-0000-4000-8000-000000000000",
    appearance.settings,
    appearance.name || "Tu asistente",
  ).replace("<script ", `<script data-preview="true" data-theme="${theme}" `);
  return (
    <aside className="wizard-preview" aria-label="Vista visual del widget">
      <h4>Vista del asistente</h4>
      <iframe
        title="Vista visual del chatbot"
        className="widget-preview-frame"
        srcDoc={`<!doctype html><html lang="es"><head><title>Vista visual del chatbot</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{height:100%;margin:0}</style></head><body>${script}</body></html>`}
      />
      <p>Vista de apariencia. En Publicación puedes probar una conversación real.</p>
    </aside>
  );
}
