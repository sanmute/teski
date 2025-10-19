// >>> MEMORY V1 START
import type { WarmupResponse } from "../types/memory";

export async function fetchWarmup(count = 2): Promise<WarmupResponse> {
  const response = await fetch(`/api/v1/memory/review/next?count=${count}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("warmup_fetch_failed");
  return (await response.json()) as WarmupResponse;
}

export async function sendReviewResult(template_code: string, correct: boolean) {
  const response = await fetch(
    `/api/v1/memory/review/result?template_code=${encodeURIComponent(template_code)}&correct=${correct}`,
    {
      method: "POST",
      credentials: "include",
    },
  );
  if (!response.ok) throw new Error("review_result_failed");
  return response.json();
}
// <<< MEMORY V1 END
