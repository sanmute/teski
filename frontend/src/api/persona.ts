import { apiFetch } from "./client";

// >>> PERSONA START
export async function listPersonas() {
  const data = await apiFetch<{ items: { code: string; displayName: string }[] }>("/api/v1/personas/");
  return data.items;
}

export async function fetchPersona(code: string) {
  const data = await apiFetch<{ config: unknown }>(`/api/v1/personas/${code}`);
  return data.config;
}

export async function previewNudge(payload: {
  requestedMood?: string | null;
  phase: "preTask" | "duringTask" | "postTaskSuccess" | "postTaskFail";
  context: {
    taskId?: number;
    minutesToDue?: number;
    overdue?: boolean;
    repeatedDeferrals?: number;
    dueAt?: string;
  };
}) {
  return apiFetch("/api/v1/personas/nudge/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
// <<< PERSONA END
