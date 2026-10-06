import { request } from "@/services/api-client";
import type { DocumentRecord } from "@/types/api";

export function listDocuments(token: string, chatbotId: string) {
  return request<DocumentRecord[]>(`/chatbots/${chatbotId}/documents`, { token });
}

export function listAvailableDocuments(token: string) {
  return request<DocumentRecord[]>("/documents", { token });
}

export function associateDocuments(
  token: string,
  chatbotId: string,
  documentIds: string[],
) {
  return request<DocumentRecord[]>(`/chatbots/${chatbotId}/documents/associations`, {
    method: "POST",
    token,
    body: JSON.stringify({ document_ids: documentIds }),
  });
}

export function removeDocumentAssociation(
  token: string,
  chatbotId: string,
  documentId: string,
) {
  return request<void>(`/chatbots/${chatbotId}/documents/${documentId}`, {
    method: "DELETE",
    token,
  });
}

export function uploadDocument(token: string, chatbotId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<DocumentRecord>(`/chatbots/${chatbotId}/documents`, {
    method: "POST",
    token,
    body,
  });
}

export function retryDocument(token: string, chatbotId: string, documentId: string) {
  return request<DocumentRecord>(
    `/chatbots/${chatbotId}/documents/${documentId}/processing`,
    { method: "POST", token },
  );
}
