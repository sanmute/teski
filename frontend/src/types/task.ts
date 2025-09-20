export interface Task {
  id: string;
  source: string;
  title: string;
  course?: string | null;
  link?: string | null;
  due_iso: string;
  status: 'open' | 'overdue' | 'done';
  confidence?: number;
  notes?: string | null;
  priority: number;
  task_type?: string | null;
  estimated_minutes?: number | null;
  suggested_start_utc?: string | null;
  completed_at?: string | null;
  signals?: Record<string, unknown> | null;
}

// Single adaptive persona - no need for persona types anymore
// The persona adapts its attitude based on task urgency
