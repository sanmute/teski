// >>> MEMORY V1 START
import type { WarmupResponse } from "../types/memory";
import { apiFetch } from "./client";

export async function fetchWarmup(count = 2): Promise<WarmupResponse> {
  return apiFetch<WarmupResponse>(`/api/v1/memory/review/next?count=${count}`, {
    credentials: "include",
  });
}

export async function sendReviewResult(template_code: string, correct: boolean) {
  return apiFetch(
    `/api/v1/memory/review/result?template_code=${encodeURIComponent(template_code)}&correct=${correct}`,
    {
      method: "POST",
      credentials: "include",
    },
  );
}
// <<< MEMORY V1 END
