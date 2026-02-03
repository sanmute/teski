import { Task } from "@/types/tasks";
import { getClientUserId } from "@/lib/user";
import { apiFetch, API_BASE } from "./client";
import { DEMO_MODE } from "@/config/demo";
import { getDemoTasksSnapshot, markDemoTaskDone, addDemoTask } from "@/demo/state";

export async function fetchUpcomingTasks(): Promise<Task[]> {
  if (DEMO_MODE) {
    return Promise.resolve(getDemoTasksSnapshot().upcoming);
  }
  return apiFetch<Task[]>(`${API_BASE}/tasks/upcoming`, {
    headers: {
      "X-User-Id": getClientUserId(),
    },
  });
}

export async function markTaskDone(taskId: number): Promise<void> {
  if (DEMO_MODE) {
    markDemoTaskDone(taskId);
    return Promise.resolve();
  }
  await apiFetch(`${API_BASE}/tasks/${taskId}/status`, {
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
  if (DEMO_MODE) {
    return Promise.resolve(addDemoTask(payload));
  }
  return apiFetch<Task>(`${API_BASE}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify(payload),
  });
}
