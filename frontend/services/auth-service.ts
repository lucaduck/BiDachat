import { request } from "@/services/api-client";
import type { LoginRequest, SessionResponse } from "@/types/api";
export function login(credentials: LoginRequest) {
  return request<SessionResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}
export function logout(token: string) {
  return request<void>("/auth/logout", { method: "POST", token });
}
