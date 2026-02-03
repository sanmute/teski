import { api } from "./client";
import { DEMO_MODE } from "@/config/demo";

export type FeedbackPayload = {
  kind: "feedback" | "bug" | "idea";
  message: string;
  severity?: "low" | "medium" | "high";
  page?: string;
  page_url?: string;
  user_agent?: string;
  app_version?: string;
  metadata?: Record<string, unknown>;
  raffle_opt_in?: boolean;
  raffle_name?: string | null;
  raffle_email?: string | null;
};

export async function submitFeedback(payload: FeedbackPayload): Promise<{ ok: boolean; id: number }> {
  if (DEMO_MODE) {
    return Promise.resolve({ ok: true, id: Date.now() % 100000 });
  }
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
   raffle_opt_in: boolean;
   raffle_name: string | null;
   raffle_email: string | null;
  created_at: string;
};

export async function getAllFeedback(limit = 50): Promise<{ ok: boolean; items: FeedbackItem[]; total: number }> {
  if (DEMO_MODE) {
    return Promise.resolve({ ok: true, items: [], total: 0 });
  }
  return api.get<{ ok: boolean; items: FeedbackItem[]; total: number }>(`/api/feedback/list?limit=${limit}`);
}
