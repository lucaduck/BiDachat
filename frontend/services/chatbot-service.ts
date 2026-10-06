import { request } from "@/services/api-client";
import type { Chatbot, ChatbotPayload, LlmModel } from "@/types/api";
export function listChatbots(token: string) {
  return request<Chatbot[]>("/chatbots", { token });
}

export function listLlmModels(token: string) {
  return request<LlmModel[]>("/llm-models", { token });
}

export function createChatbot(token: string, payload: ChatbotPayload) {
  return request<Chatbot>("/chatbots", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export function updateChatbot(
  token: string,
  chatbotId: string,
  payload: ChatbotPayload,
) {
  return request<Chatbot>(`/chatbots/${chatbotId}`, {
    method: "PUT",
    token,
    body: JSON.stringify(payload),
  });
}

export function deleteChatbot(token: string, chatbotId: string) {
  return request<void>(`/chatbots/${chatbotId}`, { method: "DELETE", token });
}
