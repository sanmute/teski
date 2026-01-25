import { Task } from "@/types/tasks";
import { getClientUserId } from "@/lib/user";
import { apiFetch } from "./client";

export async function fetchUpcomingTasks(): Promise<Task[]> {
  return apiFetch<Task[]>("/tasks/upcoming", {
    headers: {
      "X-User-Id": getClientUserId(),
    },
  });
}

export async function markTaskDone(taskId: number): Promise<void> {
  await apiFetch(`/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify({ status: "done" }),
  });
}

export interface TaskCreatePayload {
  title: string;
  course?: string | null;
  kind?: string | null;
  due_at?: string | null;
  base_estimated_minutes: number;
}

export async function createTask(payload: TaskCreatePayload): Promise<Task> {
  return apiFetch<Task>("/tasks", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify(payload),
  });
}
