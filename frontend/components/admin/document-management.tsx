"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { SelectField } from "@/components/ui/field";
import { Alert, EmptyState, LoadingState } from "@/components/ui/status";
import {
  listDocuments,
  retryDocument,
  uploadDocument,
} from "@/services/document-service";
import { validateDocument } from "@/services/document-validation";
import { documentFailure } from "@/services/document-failure";
import type { Chatbot, DocumentRecord } from "@/types/api";

function documentStatus(status: string) {
  if (status === "ready") return "Listo";
  if (status === "processing") return "Procesando";
  if (status === "failed") return "Error de procesamiento";
  return "Pendiente";
}

type Props = {
  initialChatbotId?: string;
  onSelectionChange: (id: string) => void;
  chatbots: Chatbot[];
  token: string;
  onApiError: (error: unknown) => void;
  onChanged: (message: string) => void;
};

export function DocumentManagement({
  chatbots,
  initialChatbotId,
  onSelectionChange,
  token,
  onApiError,
  onChanged,
}: Readonly<Props>) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [chatbotId, setChatbotId] = useState(
    chatbots.some((bot) => bot.id === initialChatbotId)
      ? initialChatbotId!
      : (chatbots[0]?.id ?? ""),
  );
  const [documents, setDocuments] = useState<DocumentRecord[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!chatbotId) return;
    let active = true;
    listDocuments(token, chatbotId)
      .then((records) => {
        if (active) {
          setDocuments(records);
        }
      })
      .catch((requestError) => {
        if (active) {
          onApiError(requestError);
          setError("No se pudieron cargar los documentos. Inténtalo nuevamente.");
        }
      });
    return () => {
      active = false;
    };
  }, [chatbotId, onApiError, reloadKey, token]);

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Selecciona un documento.");
      return;
    }
    const validationError = validateDocument(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await uploadDocument(token, chatbotId, file);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setReloadKey((key) => key + 1);
      if (uploaded.status === "ready") onChanged("Documento cargado y procesado.");
      else if (uploaded.status === "failed")
        setError(documentFailure(uploaded.error_code));
      else onChanged("Documento cargado. El procesamiento continúa.");
    } catch (requestError) {
      onApiError(requestError);
      setError(
        "No se pudo cargar el documento. Verifica el tipo y el tamaño e inténtalo nuevamente.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function retryProcessing(documentId: string) {
    setRetryingId(documentId);
    setError(null);
    try {
      const processed = await retryDocument(token, chatbotId, documentId);
      setDocuments(
        (items) =>
          items?.map((item) => (item.id === documentId ? processed : item)) ?? null,
      );
      if (processed.status === "ready") onChanged("Documento procesado correctamente.");
      else if (processed.status === "failed")
        setError(documentFailure(processed.error_code));
    } catch (requestError) {
      onApiError(requestError);
      setError("No se pudo reintentar el procesamiento del documento.");
    } finally {
      setRetryingId(null);
    }
  }

  if (chatbots.length === 0)
    return (
      <EmptyState
        title="No hay chatbots"
        description="Crea un chatbot antes de asociar documentos."
      />
    );

  return (
    <section aria-label="Documentos">
      <div className="section-heading">
        <div>
          <h2>Fuentes de conocimiento</h2>
          <p>Los archivos se asocian únicamente al chatbot seleccionado.</p>
        </div>
        <Button
          variant="secondary"
          type="button"
          onClick={() => {
            setDocuments(null);
            setError(null);
            setReloadKey((key) => key + 1);
          }}
        >
          Actualizar estados
        </Button>
      </div>
      <div className="section-controls">
        <SelectField
          id="document-chatbot"
          label="Chatbot"
          value={chatbotId}
          onChange={(event) => {
            setChatbotId(event.target.value);
            onSelectionChange(event.target.value);
            setDocuments(null);
            setFile(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
            setError(null);
          }}
        >
          {chatbots.map((chatbot) => (
            <option key={chatbot.id} value={chatbot.id}>
              {chatbot.name}
            </option>
          ))}
        </SelectField>
      </div>
      <form
        className="content-panel upload-form"
        onSubmit={(event) => void submitUpload(event)}
      >
        <div className="upload-heading">
          <Icon name="upload" />
          <div>
            <h3>Cargar documento o imagen</h3>
            <p>Asocia una fuente al chatbot seleccionado.</p>
          </div>
        </div>
        <label className="field upload-zone" htmlFor="document-file">
          <span>Archivo</span>
          <input
            ref={fileInputRef}
            id="document-file"
            aria-label="Archivo"
            aria-describedby="document-file-help"
            className="sr-only"
            type="file"
            accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.webp"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            disabled={isUploading}
          />
          <span className="file-picker">
            <span className="button button-secondary">
              <Icon name="upload" />
              Seleccionar archivo
            </span>
            <span>{file?.name ?? "Ningún archivo seleccionado"}</span>
          </span>
          <span id="document-file-help" className="field-hint">
            PDF, DOCX, TXT o CSV · 20 MB. PNG, JPEG o WebP · 4 MB.
          </span>
        </label>
        <Button type="submit" isLoading={isUploading} disabled={!file}>
          {isUploading ? "Subiendo documento…" : "Cargar documento"}
        </Button>
      </form>
      {error ? <Alert tone="error">{error}</Alert> : null}
      {documents === null && !error ? (
        <LoadingState label="Cargando documentos…" />
      ) : null}
      {documents?.length === 0 ? (
        <EmptyState
          title="Sin documentos"
          description="Carga una fuente de conocimiento para este chatbot."
        />
      ) : null}
      {documents && documents.length > 0 ? (
        <ul className="document-list">
          {documents.map((document) => (
            <li key={document.id}>
              <span className="document-icon">
                <Icon name="file" />
              </span>
              <div>
                <strong>{document.original_filename}</strong>
                <span>{(document.size_bytes / 1024).toFixed(1)} KB</span>
              </div>
              <span className={`document-status status-${document.status}`}>
                {documentStatus(document.status)}
              </span>
              {document.status === "failed" ? (
                <div className="document-failure">
                  <small>{documentFailure(document.error_code)}</small>
                  <Button
                    type="button"
                    variant="secondary"
                    isLoading={retryingId === document.id}
                    disabled={isUploading || retryingId !== null}
                    onClick={() => void retryProcessing(document.id)}
                  >
                    Reintentar procesamiento
                  </Button>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
