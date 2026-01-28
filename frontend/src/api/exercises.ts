import { api, API_BASE } from "./client";

export type Exercise = {
  id: string;
  question_text: string;
  type: string;
  choices: string[];
  difficulty: number;
  skill_ids: string[];
  solution_explanation?: string | null;
  hint?: string | null;
  metadata?: Record<string, unknown>;
  correct_answer?: string | null;
};

export type ExerciseListResponse = {
  items: Exercise[];
};

export async function listExercises(params: {
  user_id?: string;
  difficulty_min?: number;
  difficulty_max?: number;
  skill_id?: string;
  limit?: number;
}): Promise<ExerciseListResponse> {
  const search = new URLSearchParams();
  if (params.user_id) search.set("user_id", params.user_id);
  if (params.difficulty_min) search.set("difficulty_min", String(params.difficulty_min));
  if (params.difficulty_max) search.set("difficulty_max", String(params.difficulty_max));
  if (params.skill_id) search.set("skill_id", params.skill_id);
  if (params.limit) search.set("limit", String(params.limit));
  return api.get<ExerciseListResponse>(`/api/ex/list?${search.toString()}`);
}

export async function getExercise(id: string): Promise<Exercise> {
  return api.get<Exercise>(`/api/ex/get?id=${encodeURIComponent(id)}`);
}

export type GradeIn = {
  user_id: string;
  exercise_id: string;
  answer: unknown;
};

export type GradeOut = {
  ok: boolean;
  exercise_id: string;
  is_correct: boolean;
  correct_answer: string;
  solution_explanation?: string | null;
  hint?: string | null;
  mistake?: { family: string; subtype: string; label: string } | null;
  xp_delta: number;
  next_recommendation?: Record<string, unknown> | null;
};

export async function submitExerciseAnswer(payload: GradeIn): Promise<GradeOut> {
  return api.post<GradeOut>("/api/ex/answer", payload);
}

// Optional seed trigger for dev/admin flows
export async function seedExercises(path?: string, adminKey?: string): Promise<{ ok: boolean }> {
  const headers: Record<string, string> = {};
  if (adminKey) headers["X-Admin-Key"] = adminKey;
  const url = path ? `/api/ex/seed?path=${encodeURIComponent(path)}` : "/api/ex/seed";
  return api.post<{ ok: boolean }>(url, undefined, { headers });
}

export const EXERCISES_API_BASE = `${API_BASE}/ex`;
