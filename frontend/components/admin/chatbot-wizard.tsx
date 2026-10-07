"use client";
import "./chatbot-wizard/wizard.css";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";

import { Icon } from "@/components/ui/icon";
import { Alert } from "@/components/ui/status";
import { createChatbot, updateChatbot } from "@/services/chatbot-service";
import {
  associateDocuments,
  listAvailableDocuments,
  listDocuments,
  removeDocumentAssociation,
  uploadDocument,
} from "@/services/document-service";
import { validateDocument } from "@/services/document-validation";
import { documentFailure } from "@/services/document-failure";
import {
  DEFAULT_WIDGET_SETTINGS,
  getWidgetSettings,
  integrationScript,
  toWidgetSettingsApi,
  type WidgetSettings,
} from "@/services/widget-settings";
import type { Chatbot, ChatbotPayload, DocumentRecord, LlmModel } from "@/types/api";

import { EDITOR_STEPS as STEPS } from "@/lib/navigation";
import {
  GeneralFields,
  AppearanceFields,
  BehaviorFields,
} from "./chatbot-wizard/editor-fields";
import { KnowledgeSources } from "./chatbot-wizard/knowledge-sources";
import { WizardActions } from "./chatbot-wizard/wizard-actions";

type Props = {
  chatbot?: Chatbot;
  initialStep?: number;
  onStepChange: (step: number) => void;
  onDirtyChange: (dirty: boolean) => void;
  onSaved: (chatbot: Chatbot, step: number) => void;
  models: LlmModel[];
  token: string;
  onApiError: (error: unknown) => void;
  onClose: (changed: boolean) => void;
};

export function ChatbotWizard({
  chatbot,
  initialStep = 0,
  onStepChange,
  onDirtyChange,
  onSaved,
  models,
  token,
  onApiError,
  onClose,
}: Readonly<Props>) {
  const step = initialStep;
  function setStep(next: number | ((value: number) => number)) {
    onStepChange(typeof next === "function" ? next(step) : next);
  }
  const [draft, setDraft] = useState<ChatbotPayload>({
    name: chatbot?.name ?? "",
    description: chatbot?.description ?? null,
    behavior_instructions: chatbot?.behavior_instructions ?? "",
    configured_llm_model_id: chatbot?.configured_llm_model.id ?? models[0]?.id ?? "",
  });
  const [settings, setSettings] = useState<WidgetSettings>(() =>
    chatbot ? getWidgetSettings(chatbot.widget_settings) : DEFAULT_WIDGET_SETTINGS,
  );
  const [savedId, setSavedId] = useState(chatbot?.id ?? "");
  const [hasChanges, setHasChanges] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const stepsRef = useRef<HTMLOListElement>(null);
  useEffect(() => {
    const list = stepsRef.current;
    if (!list) return;
    function revealCurrentStep() {
      const current = list?.querySelector<HTMLElement>('[aria-current="step"]');
      if (!current || !list || list.scrollWidth <= list.clientWidth) return;
      const offset =
        current.getBoundingClientRect().left -
        list.getBoundingClientRect().left +
        list.scrollLeft;
      list.scrollLeft = offset - (list.clientWidth - current.offsetWidth) / 2;
    }
    revealCurrentStep();
    const observer = new ResizeObserver(revealCurrentStep);
    observer.observe(list);
    return () => observer.disconnect();
  }, [step]);
  const [documents, setDocuments] = useState<DocumentRecord[] | null>(null);
  const [availableDocuments, setAvailableDocuments] = useState<DocumentRecord[] | null>(
    null,
  );
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const fingerprint = JSON.stringify({ draft, settings });
  const [savedFingerprint, setSavedFingerprint] = useState(fingerprint);
  const dirty = fingerprint !== savedFingerprint;
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  const origin =
    typeof window === "undefined" ? "http://localhost:3000" : window.location.origin;
  const script = savedId
    ? integrationScript(origin, savedId, settings, draft.name)
    : "";
  const previewParams = new URLSearchParams({
    chatbot_id: savedId,
    color: settings.primaryColor,
    icon: settings.icon,
    title: draft.name,
    welcome: settings.welcomeMessage,
  });
  previewParams.set("editor_step", "4");

  useEffect(() => {
    if (step !== 3 || !savedId) return;
    let active = true;
    Promise.all([listDocuments(token, savedId), listAvailableDocuments(token)])
      .then(([items, available]) => {
        if (active) setDocuments(items);
        if (active) setAvailableDocuments(available);
      })
      .catch((requestError) => {
        if (active) {
          onApiError(requestError);
          setDocuments([]);
          setAvailableDocuments([]);
          setError(
            "No se pudo cargar la lista de documentos. Puedes continuar y revisarla más tarde.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [onApiError, savedId, step, token]);

  function advance(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    setError(null);
    if (step === 0 && !draft.name.trim()) {
      setError("Indica el nombre del chatbot para continuar.");
      return;
    }
    if (step === 2) {
      void saveAndAdvance();
      return;
    }
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  }

  async function saveAndAdvance() {
    if (!draft.name.trim()) {
      setError("Indica el nombre del chatbot en Información general.");
      setStep(0);
      return;
    }
    if (!draft.configured_llm_model_id) {
      setError("Selecciona un modelo de lenguaje.");
      return;
    }
    setBusy(true);
    try {
      const payload = {
        ...draft,
        name: draft.name.trim(),
        description: draft.description?.trim() || null,
        behavior_instructions: draft.behavior_instructions.trim(),
        widget_settings: toWidgetSettingsApi(settings),
      };
      const saved = savedId
        ? await updateChatbot(token, savedId, payload)
        : await createChatbot(token, payload);
      setSavedId(saved.id);
      setHasChanges(true);
      setNotice("Configuración guardada. Puedes asociar documentos ahora.");
      setSavedFingerprint(fingerprint);
      onSaved(saved, 3);
    } catch (requestError) {
      onApiError(requestError);
      setError(
        "No se pudo guardar el chatbot. Revisa los datos e inténtalo nuevamente.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function addDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !savedId) return;
    const validationError = validateDocument(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const document = await uploadDocument(token, savedId, file);
      setDocuments((items) => [...(items ?? []), document]);
      setAvailableDocuments((items) => [...(items ?? []), document]);
      setHasChanges(true);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (document.status === "ready") setNotice("Documento procesado correctamente.");
      else if (document.status === "failed")
        setError(documentFailure(document.error_code));
      else setNotice("Documento cargado. Consulta su estado en Documentos y RAG.");
    } catch (requestError) {
      onApiError(requestError);
      setError(
        "No se pudo cargar el documento. Verifica el archivo e inténtalo de nuevo.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function addExistingDocuments() {
    if (!savedId || selectedDocumentIds.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      await associateDocuments(token, savedId, selectedDocumentIds);
      const items = await listDocuments(token, savedId);
      setDocuments(items);
      setSelectedDocumentIds([]);
      setHasChanges(true);
      setNotice("Documentos asociados al chatbot.");
    } catch (requestError) {
      onApiError(requestError);
      setError("No se pudieron asociar los documentos seleccionados.");
    } finally {
      setBusy(false);
    }
  }

  async function removeDocument(documentId: string) {
    if (!savedId) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await removeDocumentAssociation(token, savedId, documentId);
      setDocuments((items) => items?.filter((item) => item.id !== documentId) ?? []);
      setSelectedDocumentIds((items) => items.filter((id) => id !== documentId));
      setHasChanges(true);
      setNotice("Fuente quitada del contexto. Puedes asociarla nuevamente.");
    } catch (requestError) {
      onApiError(requestError);
      setError("No se pudo quitar la fuente del contexto.");
    } finally {
      setBusy(false);
    }
  }

  function close() {
    if (busy) return;
    onClose(hasChanges);
  }

  return (
    <section className="wizard" aria-labelledby="wizard-title">
      <div className="wizard-heading">
        <div>
          <h2 id="wizard-title">
            {chatbot ? "Editar chatbot" : "Crear nuevo chatbot"}
          </h2>
          <p>
            Configura el asistente paso a paso y revisa el resultado antes de
            publicarlo.
          </p>
        </div>
        <span className="wizard-count">
          Paso {step + 1} de {STEPS.length}
        </span>
      </div>
      <ol
        ref={stepsRef}
        className="wizard-steps"
        aria-label="Pasos de configuración"
        tabIndex={0}
      >
        {STEPS.map((label, index) => (
          <li
            key={label}
            aria-current={step === index ? "step" : undefined}
            data-complete={index < step}
          >
            <span>{index < step ? <Icon name="check" /> : index + 1}</span>
            {label}
          </li>
        ))}
      </ol>
      {error ? <Alert tone="error">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}

      {step === 0 ? (
        <form className="wizard-content" onSubmit={advance}>
          <div className="wizard-section-heading">
            <h3>Información general</h3>
            <p>Define la identidad básica del asistente.</p>
          </div>
          <GeneralFields draft={draft} setDraft={setDraft} />
          <WizardActions step={step} busy={busy} onBack={close} />
        </form>
      ) : null}

      {step === 1 ? (
        <form className="wizard-content" onSubmit={advance}>
          <div className="wizard-section-heading">
            <h3>Apariencia</h3>
            <p>El color, el icono y el saludo aparecerán en el widget integrado.</p>
          </div>
          <AppearanceFields
            draft={draft}
            settings={settings}
            setSettings={setSettings}
          />
          <WizardActions step={step} busy={busy} onBack={() => setStep(0)} />
        </form>
      ) : null}

      {step === 2 ? (
        <form className="wizard-content" onSubmit={advance}>
          <div className="wizard-section-heading">
            <h3>Comportamiento e IA</h3>
            <p>Selecciona el modelo y define cómo debe responder el chatbot.</p>
          </div>
          <fieldset disabled={busy} className="wizard-fieldset">
            <BehaviorFields
              draft={draft}
              setDraft={setDraft}
              settings={settings}
              setSettings={setSettings}
              models={models}
            />
          </fieldset>
          <WizardActions step={step} busy={busy} onBack={() => setStep(1)} />
        </form>
      ) : null}

      {step === 3 ? (
        <div className="wizard-content">
          <div className="wizard-section-heading">
            <h3>Base de conocimiento</h3>
            <p>
              Asocia documentos e imágenes al chatbot. Puedes continuar sin fuentes y
              cargarlas después.
            </p>
          </div>
          <KnowledgeSources
            fileInputRef={fileInputRef}
            file={file}
            busy={busy}
            documents={documents}
            availableDocuments={availableDocuments}
            selectedDocumentIds={selectedDocumentIds}
            onUpload={(event) => void addDocument(event)}
            onRemove={(id) => void removeDocument(id)}
            onFile={setFile}
            onSelect={(id, selected) =>
              setSelectedDocumentIds((items) =>
                selected ? [...items, id] : items.filter((item) => item !== id),
              )
            }
            onAssociate={() => void addExistingDocuments()}
          />
          <div className="wizard-actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setStep(2)}
              disabled={busy}
            >
              Anterior
            </Button>
            <Button
              type="button"
              disabled={busy}
              onClick={() => {
                setNotice(null);
                setStep(4);
              }}
            >
              Siguiente paso
            </Button>
          </div>
        </div>
      ) : null}

      {step === 4 ? (
        <div className="wizard-content">
          <div className="wizard-published">
            <span className="wizard-success">
              <Icon name="check" />
            </span>
            <h3>Tu asistente está listo</h3>
            <p>
              Revisa el widget en un dashboard de ejemplo antes de copiar el código.
            </p>
          </div>
          <div className="wizard-card wizard-publication">
            <h4>Vista previa del widget</h4>
            <p>Comprueba el color, el icono y el saludo en el widget real.</p>
            <a
              className="button button-secondary"
              href={`/preview?${previewParams.toString()}`}
            >
              Abrir vista previa
            </a>
          </div>
          <div className="wizard-card wizard-publication">
            <div className="publication-heading">
              <h4>Script de instalación</h4>
              <Button
                type="button"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(script);
                    setCopied(true);
                  } catch {
                    setError(
                      "No se pudo copiar el script. Selecciona el código y cópialo manualmente.",
                    );
                  }
                }}
              >
                {copied ? "Copiado" : "Copiar código"}
              </Button>
            </div>
            <p>
              Pega este código antes de la etiqueta de cierre <code>&lt;/body&gt;</code>{" "}
              del dashboard.
            </p>
            {chatbot ? (
              <p>
                Si el dashboard ya tiene un script de este chatbot, reemplázalo para
                aplicar los cambios de apariencia.
              </p>
            ) : null}
            <textarea
              aria-label="Script de integración"
              readOnly
              rows={5}
              value={script}
              onFocus={(event) => event.currentTarget.select()}
            />
          </div>
          <div className="wizard-actions">
            <Button type="button" variant="secondary" onClick={() => setStep(3)}>
              Anterior
            </Button>
            <div className="wizard-action-group">
              <Button type="button" onClick={close}>
                Finalizar
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
