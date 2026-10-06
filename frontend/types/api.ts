export type LoginRequest = { email: string; password: string };
export type SessionResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
};
export type Chatbot = {
  id: string;
  name: string;
  description: string | null;
  behavior_instructions: string;
  widget_settings: WidgetSettingsApi;
  configured_llm_model: { id: string; provider: string; model: string };
  created_at: string;
  updated_at: string;
};

export type LlmModel = { id: string; provider: string; model: string };

export type ChatbotPayload = {
  name: string;
  description: string | null;
  behavior_instructions: string;
  configured_llm_model_id: string;
  widget_settings?: WidgetSettingsApi;
};

export type WidgetSettingsApi = {
  primary_color: string;
  icon: "bot" | "chat" | "chart" | "book" | "sparkles" | "headset";
  welcome_message: string;
};

export type DocumentRecord = {
  id: string;
  chatbot_id: string;
  original_filename: string;
  media_type: string;
  size_bytes: number;
  status: string;
  error_code: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
};

export type MetricsPoint = {
  period_start: string;
  total_queries: number;
  completed_queries: number;
  failed_queries: number;
  processing_queries: number;
  measured_response_count: number;
  average_response_time_ms: number | null;
};
export type MetricsSummary = {
  chatbot_id: string;
  started_at: string | null;
  ended_at: string | null;
  total_queries: number;
  completed_queries: number;
  failed_queries: number;
  processing_queries: number;
  measured_response_count: number;
  average_response_time_ms: number | null;
  interval: "day" | "week" | "month";
  status: "completed" | "failed" | "processing" | null;
  series: MetricsPoint[];
};
