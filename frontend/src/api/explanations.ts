import { ExplanationResponse } from "@/types/explanations";
import { getClientUserId } from "@/lib/user";

export async function generateExplanation(text: string, mode: string = "auto"): Promise<ExplanationResponse> {
  const res = await fetch(`/explanations/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify({ text, mode }),
  });

  if (!res.ok) {
    throw new Error("Failed to generate explanation");
  }

  return res.json();
}
