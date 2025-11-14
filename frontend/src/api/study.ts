import {
  StudySessionCompleteRequest,
  StudySessionDetailResponse,
  StudySessionStartResponse,
} from "@/types/study";
import { getClientUserId } from "@/lib/user";

export async function startStudySession(
  taskBlockId: number,
  goalText?: string
): Promise<StudySessionStartResponse> {
  const res = await fetch(`/study/sessions/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify({ task_block_id: taskBlockId, goal_text: goalText ?? null }),
  });
  if (!res.ok) {
    throw new Error("Failed to start study session");
  }
  return res.json();
}

export async function fetchStudySession(sessionId: number): Promise<StudySessionDetailResponse> {
  const res = await fetch(`/study/sessions/${sessionId}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch study session");
  }
  return res.json();
}

export async function completeStudySession(
  sessionId: number,
  payload: StudySessionCompleteRequest
) {
  const res = await fetch(`/study/sessions/${sessionId}/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error("Failed to complete study session");
  }
  return res.json();
}
