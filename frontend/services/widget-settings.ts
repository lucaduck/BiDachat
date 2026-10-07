import type { WidgetSettingsApi } from "@/types/api";

export type WidgetSettings = {
  primaryColor: string;
  icon: WidgetSettingsApi["icon"];
  welcomeMessage: string;
};

export const DEFAULT_WIDGET_SETTINGS: WidgetSettings = {
  primaryColor: "#14a8ce",
  icon: "bot",
  welcomeMessage: "Hola, ¿en qué puedo ayudarte con este dashboard?",
};

export function getWidgetSettings(value?: WidgetSettingsApi): WidgetSettings {
  return {
    primaryColor: isHexColor(value?.primary_color)
      ? value.primary_color
      : DEFAULT_WIDGET_SETTINGS.primaryColor,
    icon: isWidgetIcon(value?.icon) ? value.icon : DEFAULT_WIDGET_SETTINGS.icon,
    welcomeMessage:
      typeof value?.welcome_message === "string" && value.welcome_message.length <= 300
        ? value.welcome_message
        : DEFAULT_WIDGET_SETTINGS.welcomeMessage,
  };
}

export function toWidgetSettingsApi(settings: WidgetSettings): WidgetSettingsApi {
  return {
    primary_color: settings.primaryColor,
    icon: settings.icon,
    welcome_message: settings.welcomeMessage,
  };
}

export function isHexColor(value: unknown): value is string {
  return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
}

export function isWidgetIcon(value: unknown): value is WidgetSettings["icon"] {
  return (
    typeof value === "string" &&
    ["bot", "chat", "chart", "book", "sparkles", "headset"].includes(value)
  );
}

export function integrationScript(
  origin: string,
  chatbotId: string,
  settings: WidgetSettings,
  chatbotName = "BIDACHAT",
) {
  const script = new URL("/bidachat-widget.js", origin).href;
  return `<script src="${script}" data-chatbot-id="${chatbotId}" data-title="${escapeAttribute(chatbotName)}" data-primary-color="${settings.primaryColor}" data-icon="${settings.icon}" data-welcome-message="${escapeAttribute(settings.welcomeMessage)}" data-context-selector="main"></script>`;
}

export function contrastTextColor(hex: string) {
  if (!isHexColor(hex)) return "#08111f";
  const channels = [1, 3, 5].map(
    (index) => parseInt(hex.slice(index, index + 2), 16) / 255,
  );
  const luminance = channels
    .map((value) =>
      value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4,
    )
    .reduce(
      (total, value, index) => total + value * [0.2126, 0.7152, 0.0722][index],
      0,
    );
  return luminance > 0.18 ? "#08111f" : "#ffffff";
}

function escapeAttribute(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
