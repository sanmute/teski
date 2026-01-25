import {
  StudySessionCompleteRequest,
  StudySessionDetailResponse,
  StudySessionStartResponse,
} from "@/types/study";
import { getClientUserId } from "@/lib/user";
import { apiFetch } from "./client";

export async function startStudySession(
  taskBlockId: number,
  goalText?: string
): Promise<StudySessionStartResponse> {
  return apiFetch<StudySessionStartResponse>("/study/sessions/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify({ task_block_id: taskBlockId, goal_text: goalText ?? null }),
  });
}

export async function fetchStudySession(sessionId: number): Promise<StudySessionDetailResponse> {
  return apiFetch<StudySessionDetailResponse>(`/study/sessions/${sessionId}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
}

export async function completeStudySession(
  sessionId: number,
  payload: StudySessionCompleteRequest
) {
  return apiFetch(`/study/sessions/${sessionId}/complete`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify(payload),
  });
}
