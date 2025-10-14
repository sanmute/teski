// >>> PERSONA START
export async function listPersonas() {
  const response = await fetch("/api/v1/personas/");
  if (!response.ok) throw new Error("persona_list_failed");
  return (await response.json()).items as { code: string; displayName: string }[];
}

export async function fetchPersona(code: string) {
  const response = await fetch(`/api/v1/personas/${code}`);
  if (!response.ok) throw new Error("persona_fetch_failed");
  return (await response.json()).config;
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
  const response = await fetch("/api/v1/personas/nudge/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("nudge_preview_failed");
  return await response.json();
}
// <<< PERSONA END
