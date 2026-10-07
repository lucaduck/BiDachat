import { useState, type Dispatch, type SetStateAction } from "react";
import { InputField, SelectField, TextareaField } from "@/components/ui/field";
import type { ChatbotPayload, LlmModel } from "@/types/api";
import type { WidgetSettings } from "@/services/widget-settings";
import { WidgetPreview } from "./widget-preview";
import { AppearanceOptions } from "./appearance-options";
type Props = {
  draft: ChatbotPayload;
  setDraft: Dispatch<SetStateAction<ChatbotPayload>>;
  settings: WidgetSettings;
  setSettings: Dispatch<SetStateAction<WidgetSettings>>;
  models: LlmModel[];
};
const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  openrouter: "OpenRouter",
  ollama: "Ollama",
  gemini: "Gemini",
};
export function GeneralFields({
  draft,
  setDraft,
}: Readonly<Pick<Props, "draft" | "setDraft">>) {
  return (
    <>
      <div className="wizard-card wizard-narrow">
        <InputField
          id="wizard-name"
          label="Nombre del chatbot"
          value={draft.name}
          onChange={(event) =>
            setDraft((value) => ({ ...value, name: event.target.value }))
          }
          maxLength={200}
          required
        />
        <TextareaField
          id="wizard-description"
          label="Descripción"
          value={draft.description ?? ""}
          onChange={(event) =>
            setDraft((value) => ({ ...value, description: event.target.value }))
          }
          maxLength={2000}
        />
      </div>
    </>
  );
}
export function AppearanceFields({
  draft,
  settings,
  setSettings,
}: Readonly<Pick<Props, "draft" | "settings" | "setSettings">>) {
  return (
    <>
      <div className="wizard-columns">
        <div className="wizard-card">
          <label className="field" htmlFor="widget-color">
            Color principal
            <span className="color-control">
              <input
                id="widget-color"
                type="color"
                value={settings.primaryColor}
                onChange={(event) =>
                  setSettings((value) => ({
                    ...value,
                    primaryColor: event.target.value,
                  }))
                }
              />
              <span>{settings.primaryColor.toUpperCase()}</span>
            </span>
          </label>
          <p className="appearance-hint">
            Elige una propuesta o ajusta el color principal.
          </p>
          <AppearanceOptions settings={settings} setSettings={setSettings} />
        </div>
        <WidgetPreview name={draft.name} settings={settings} />
      </div>
    </>
  );
}
export function BehaviorFields({
  draft,
  setDraft,
  settings,
  setSettings,
  models,
}: Readonly<Props>) {
  const selectedModel = models.find(
    (model) => model.id === draft.configured_llm_model_id,
  );
  const [providerOverride, setProviderOverride] = useState<string | null>(null);
  const provider = providerOverride ?? selectedModel?.provider ?? "";
  const providers = [...new Set(models.map((model) => model.provider))];
  const providerModels = models.filter((model) => model.provider === provider);

  return (
    <>
      <div className="wizard-columns">
        <div className="wizard-card">
          <div className="wizard-model-fields">
            <SelectField
              id="wizard-provider"
              label="Proveedor de IA"
              value={provider}
              onChange={(event) => {
                setProviderOverride(event.target.value);
                setDraft((value) => ({ ...value, configured_llm_model_id: "" }));
              }}
              required
            >
              <option value="">Selecciona un proveedor</option>
              {providers.map((value) => (
                <option key={value} value={value}>
                  {PROVIDER_LABELS[value] ?? value}
                </option>
              ))}
            </SelectField>
            <SelectField
              id="wizard-model"
              label="Modelo de lenguaje"
              value={draft.configured_llm_model_id}
              onChange={(event) => {
                setProviderOverride(null);
                setDraft((value) => ({
                  ...value,
                  configured_llm_model_id: event.target.value,
                }));
              }}
              disabled={!provider}
              required
            >
              <option value="">
                {provider ? "Selecciona un modelo" : "Elige primero un proveedor"}
              </option>
              {providerModels.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.model}
                </option>
              ))}
            </SelectField>
          </div>
          <TextareaField
            id="wizard-instructions"
            label="Instrucciones de comportamiento"
            value={draft.behavior_instructions}
            onChange={(event) =>
              setDraft((value) => ({
                ...value,
                behavior_instructions: event.target.value,
              }))
            }
            maxLength={10000}
            hint="Define rol, tono y reglas. Estas instrucciones se usarán al responder consultas."
          />
          <TextareaField
            id="wizard-welcome"
            label="Mensaje de bienvenida"
            value={settings.welcomeMessage}
            onChange={(event) =>
              setSettings((value) => ({
                ...value,
                welcomeMessage: event.target.value,
              }))
            }
            maxLength={300}
            hint="Se muestra al abrir el widget."
          />
        </div>
        <WidgetPreview name={draft.name} settings={settings} />
      </div>
    </>
  );
}
