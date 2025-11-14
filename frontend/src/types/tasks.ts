export type TaskStatus = "pending" | "done";

export interface TaskBlock {
  id: number;
  task_id: number;
  duration_minutes: number;
  label: string;
  start_at?: string | null;
}

export interface Task {
  id: number;
  title: string;
  course?: string | null;
  kind?: string | null;
  due_at?: string | null;
  status: TaskStatus;
  personalized_estimated_minutes: number;
  blocks: TaskBlock[];
}
