import { request } from "@/services/api-client";

export type SystemSettings = {
  gemini_configured: boolean;
  openai_configured: boolean;
  openrouter_configured: boolean;
  embedding_provider: "gemini" | "ollama";
  embedding_model: string;
  embedding_dimensions: number;
  document_max_size_bytes: number;
  session_ttl_minutes: number;
  widget_allowed_origins: string[];
};

export function getSystemSettings(token: string) {
  return request<SystemSettings>("/settings", { token });
}
