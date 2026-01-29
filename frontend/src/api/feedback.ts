import { api } from "./client";

export type FeedbackPayload = {
  kind: "feedback" | "bug" | "idea";
  message: string;
  severity?: "low" | "medium" | "high";
  page_url?: string;
  user_agent?: string;
  app_version?: string;
  metadata?: Record<string, unknown>;
};

export async function submitFeedback(payload: FeedbackPayload): Promise<{ ok: boolean; id: number }> {
  return api.post<{ ok: boolean; id: number }>("/api/feedback/submit", payload);
}

export type FeedbackItem = {
  id: number;
  user_id: string | null;
  user_email: string | null;
  kind: string;
  message: string;
  severity: string | null;
  page_url: string | null;
  user_agent: string | null;
  app_version: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export async function getAllFeedback(limit = 50): Promise<{ ok: boolean; items: FeedbackItem[]; total: number }> {
  return api.get<{ ok: boolean; items: FeedbackItem[]; total: number }>(`/api/feedback/list?limit=${limit}`);
}
