import { ExplanationResponse } from "@/types/explanations";
import { getClientUserId } from "@/lib/user";
import { apiFetch } from "./client";

export async function generateExplanation(text: string, mode: string = "auto"): Promise<ExplanationResponse> {
  return apiFetch<ExplanationResponse>("/explanations/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify({ text, mode }),
  });
}
