export type SessionPhaseStep = {
  id: string;
  label: string;
  description?: string;
};

export type SessionPlan = {
  phase: "prepare" | "focus" | "close";
  title: string;
  steps: SessionPhaseStep[];
};

export type StudySessionStartResponse = {
  session_id: number;
  task_id: number;
  task_block_id: number;
  block_label: string;
  block_duration_minutes: number;
  task_title: string;
  course?: string | null;
  kind?: string | null;
  planned_duration_minutes: number;
  plan_prepare: SessionPlan;
  plan_focus: SessionPlan;
  plan_close: SessionPlan;
};

export type StudySessionDetailResponse = StudySessionStartResponse & {
  status: "active" | "completed" | "abandoned";
  started_at: string;
  ended_at?: string | null;
};

export type StudySessionCompleteRequest = {
  goal_completed?: boolean;
  perceived_difficulty?: number;
  time_feeling?: "too_short" | "just_right" | "too_long";
  notes?: string;
  actual_duration_minutes?: number;
};
