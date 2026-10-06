import { describe, expect, it } from "vitest";

import {
  getWidgetSettings,
  integrationScript,
  toWidgetSettingsApi,
} from "./widget-settings";

describe("widget settings", () => {
  it.each(["book", "sparkles", "headset"] as const)(
    "preserves the %s icon from the API to the integration script",
    (icon) => {
      const settings = getWidgetSettings({
        primary_color: "#e45756",
        icon,
        welcome_message: "Hola",
      });
      expect(toWidgetSettingsApi(settings).icon).toBe(icon);
      expect(
        integrationScript("https://example.org", "chatbot-id", settings),
      ).toContain(`data-icon="${icon}"`);
    },
  );

  it("maps saved appearance into the editor and embed script", () => {
    const settings = getWidgetSettings({
      primary_color: "#135bec",
      icon: "chart",
      welcome_message: "Consulta el panel",
    });
    expect(settings.primaryColor).toBe("#135bec");
    expect(toWidgetSettingsApi(settings).icon).toBe("chart");
    expect(integrationScript("https://example.org", "chatbot-id", settings)).toContain(
      'data-primary-color="#135bec"',
    );
  });

  it("escapes the greeting before placing it in an HTML attribute", () => {
    const script = integrationScript("https://example.org", "chatbot-id", {
      primaryColor: "#14a8ce",
      icon: "bot",
      welcomeMessage: 'Hola "<script>alert(1)</script>" & bienvenido',
    });
    expect(script).toContain("&quot;&lt;script&gt;alert(1)&lt;/script&gt;&quot;");
    expect(script).not.toContain('data-welcome-message="Hola "');
  });
});
