import { api } from "./client";

export type FeedbackPayload = {
  message: string;
  rating?: number;
  page?: string;
  context?: string;
};

export async function submitFeedback(payload: FeedbackPayload): Promise<void> {
  await api.post("/feedback", payload);
}

export type FeedbackItem = {
  id: string;
  user_id: string;
  created_at: string;
  page?: string | null;
  context?: string | null;
  message: string;
  rating?: number | null;
};

export async function getAllFeedback(): Promise<FeedbackItem[]> {
  return api.get<FeedbackItem[]>("/feedback");
}
