import type { Dispatch, SetStateAction } from "react";
import { Icon, type IconName } from "@/components/ui/icon";
import type { WidgetSettings } from "@/services/widget-settings";

const COLOR_OPTIONS = [
  { label: "Turquesa BIDACHAT", value: "#14a8ce" },
  { label: "Azul", value: "#2563eb" },
  { label: "Índigo", value: "#4f46e5" },
  { label: "Violeta", value: "#7c3aed" },
  { label: "Esmeralda", value: "#059669" },
  { label: "Coral", value: "#e45756" },
  { label: "Ámbar", value: "#d97706" },
  { label: "Grafito", value: "#334155" },
] as const;

const ICON_OPTIONS: {
  value: WidgetSettings["icon"];
  symbol: IconName;
  label: string;
}[] = [
  { value: "bot", symbol: "bot", label: "Robot" },
  { value: "chat", symbol: "message", label: "Conversación" },
  { value: "chart", symbol: "chart", label: "Análisis" },
  { value: "book", symbol: "book", label: "Conocimiento" },
  { value: "sparkles", symbol: "sparkles", label: "Asistente IA" },
  { value: "headset", symbol: "headset", label: "Soporte" },
];

type Props = {
  settings: WidgetSettings;
  setSettings: Dispatch<SetStateAction<WidgetSettings>>;
};

export function AppearanceOptions({ settings, setSettings }: Readonly<Props>) {
  return (
    <>
      <fieldset className="appearance-options color-options">
        <legend>Colores sugeridos</legend>
        {COLOR_OPTIONS.map(({ label, value }) => (
          <label
            key={value}
            className={`appearance-option${settings.primaryColor.toLowerCase() === value ? " selected" : ""}`}
          >
            <input
              type="radio"
              name="widget-color-preset"
              value={value}
              checked={settings.primaryColor.toLowerCase() === value}
              onChange={() =>
                setSettings((current) => ({ ...current, primaryColor: value }))
              }
            />
            <span
              className="color-swatch"
              style={{ backgroundColor: value }}
              aria-hidden="true"
            />
            <span>{label}</span>
          </label>
        ))}
      </fieldset>
      <fieldset className="appearance-options">
        <legend>Icono del bot</legend>
        {ICON_OPTIONS.map(({ value, symbol, label }) => (
          <label
            key={value}
            className={`appearance-option${settings.icon === value ? " selected" : ""}`}
          >
            <input
              type="radio"
              name="widget-icon"
              value={value}
              checked={settings.icon === value}
              onChange={() => setSettings((current) => ({ ...current, icon: value }))}
            />
            <Icon name={symbol} />
            <span>{label}</span>
          </label>
        ))}
      </fieldset>
    </>
  );
}
