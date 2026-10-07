import type { FormEvent, RefObject } from "react";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { LoadingState } from "@/components/ui/status";
import type { DocumentRecord } from "@/types/api";
type Props = {
  fileInputRef: RefObject<HTMLInputElement | null>;
  file: File | null;
  busy: boolean;
  documents: DocumentRecord[] | null;
  availableDocuments: DocumentRecord[] | null;
  selectedDocumentIds: string[];
  onUpload: (event: FormEvent<HTMLFormElement>) => void;
  onRemove: (id: string) => void;
  onFile: (file: File | null) => void;
  onSelect: (id: string, selected: boolean) => void;
  onAssociate: () => void;
};
export function KnowledgeSources({
  fileInputRef,
  file,
  busy,
  documents,
  availableDocuments,
  selectedDocumentIds,
  onUpload,
  onRemove,
  onFile,
  onSelect,
  onAssociate,
}: Readonly<Props>) {
  return (
    <>
      <form className="wizard-card wizard-narrow" onSubmit={(event) => onUpload(event)}>
        <label
          className="field upload-zone wizard-upload-zone"
          htmlFor="wizard-document"
        >
          <span>Subir documento o imagen</span>
          <input
            ref={fileInputRef}
            id="wizard-document"
            aria-label="Subir documento o imagen"
            className="sr-only"
            type="file"
            accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.webp"
            aria-describedby="wizard-document-help"
            onChange={(event) => onFile(event.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <span className="file-picker">
            <span className="button button-secondary wizard-file-button">
              <Icon name="upload" />
              Seleccionar archivo
            </span>
            <span className="wizard-file-name" data-selected={file ? true : undefined}>
              {file?.name ?? "Ningún archivo seleccionado"}
            </span>
          </span>
        </label>
        <p className="field-hint" id="wizard-document-help">
          PDF, DOCX, TXT o CSV · 20 MB. PNG, JPEG o WebP · 4 MB. Las imágenes se
          procesan como fuentes visuales para su búsqueda.
        </p>
        <Button type="submit" disabled={!file} isLoading={busy}>
          Cargar fuente
        </Button>
        {documents === null ? <LoadingState label="Cargando fuentes…" /> : null}
        {documents?.length ? (
          <ul className="wizard-document-list">
            {documents.map((document) => (
              <li key={document.id}>
                <span>
                  <strong>{document.original_filename}</strong>
                  <small>
                    {document.status === "ready"
                      ? "Lista"
                      : document.status === "failed"
                        ? "Error"
                        : "En proceso"}
                  </small>
                </span>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={busy}
                  onClick={() => onRemove(document.id)}
                >
                  Quitar del contexto
                </Button>
              </li>
            ))}
          </ul>
        ) : null}
      </form>
      {availableDocuments?.filter(
        (document) => !documents?.some((item) => item.id === document.id),
      ).length ? (
        <section className="wizard-card wizard-existing-documents">
          <div>
            <h4>Usar documentos existentes</h4>
            <p>Selecciona fuentes que ya fueron cargadas para otro chatbot.</p>
          </div>
          <div className="existing-document-list">
            {availableDocuments
              .filter((document) => !documents?.some((item) => item.id === document.id))
              .map((document) => (
                <label key={document.id} className="existing-document-option">
                  <input
                    type="checkbox"
                    checked={selectedDocumentIds.includes(document.id)}
                    onChange={(event) => onSelect(document.id, event.target.checked)}
                  />
                  <span>
                    <strong>{document.original_filename}</strong>
                    <small>
                      {document.status === "ready"
                        ? "Listo para consultar"
                        : "En procesamiento"}
                    </small>
                  </span>
                </label>
              ))}
          </div>
          <Button
            type="button"
            variant="secondary"
            disabled={selectedDocumentIds.length === 0 || busy}
            isLoading={busy}
            onClick={() => onAssociate()}
          >
            Asociar seleccionados
          </Button>
        </section>
      ) : null}
    </>
  );
}
