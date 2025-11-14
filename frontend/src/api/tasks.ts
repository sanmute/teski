import { API_BASE } from "@/api";
import { Task } from "@/types/tasks";

export async function fetchUpcomingTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/tasks/upcoming`);
  if (!res.ok) {
    throw new Error("Failed to fetch upcoming tasks");
  }
  return res.json();
}

export async function markTaskDone(taskId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "done" }),
  });
  if (!res.ok) {
    throw new Error("Failed to update task status");
  }
}

export interface TaskCreatePayload {
  title: string;
  course?: string | null;
  kind?: string | null;
  due_at?: string | null;
  base_estimated_minutes: number;
}

export async function createTask(payload: TaskCreatePayload): Promise<Task> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to create task");
  }

  return res.json();
}
