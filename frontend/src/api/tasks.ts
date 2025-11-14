import { Task } from "@/types/tasks";
import { getClientUserId } from "@/lib/user";

export async function fetchUpcomingTasks(): Promise<Task[]> {
  const res = await fetch(`/tasks/upcoming`, {
    headers: {
      "X-User-Id": getClientUserId(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch upcoming tasks");
  }
  return res.json();
}

export async function markTaskDone(taskId: number): Promise<void> {
  const res = await fetch(`/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
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
  const res = await fetch(`/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getClientUserId(),
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to create task");
  }

  return res.json();
}
