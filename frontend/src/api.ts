import { API_BASE, apiFetch } from "./api/client";
export { API_BASE_URL, apiFetch, API_BASE, getAuthToken, setAuthToken, loadAuthTokenFromStorage } from "./api/client";

// Convenience wrapper to mirror other callers; keeps single source of truth.
export const apiRequest = apiFetch;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export interface TaskResponse {
  id: string;
  source: string;
  title: string;
  course?: string | null;
  link?: string | null;
  due_iso: string;
  status: "open" | "done" | "overdue";
  confidence: number;
  notes?: string | null;
  task_type?: string | null;
  estimated_minutes?: number | null;
  suggested_start_utc?: string | null;
  priority: number;
  completed_at?: string | null;
  signals?: Record<string, unknown> | null;
}

export async function getTasks(): Promise<TaskResponse[]> {
  const res = await fetch(`${API_BASE}/tasks`);
  return handleResponse<TaskResponse[]>(res);
}

export async function markTaskDone(taskId: string): Promise<TaskResponse> {
  const res = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}/done`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<TaskResponse>(res);
}

export async function undoTask(taskId: string): Promise<TaskResponse> {
  const res = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}/undo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<TaskResponse>(res);
}

export interface ReminderResponse {
  taskId: string;
  escalation: "calm" | "snark" | "disappointed" | "intervention";
  persona: string;
  scriptHints: string;
  due_iso: string;
  title: string;
  priority: number;
}

export async function nextReminder(persona: string = "teacher"): Promise<ReminderResponse> {
  const res = await fetch(`${API_BASE}/reminders/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona }),
  });
  return handleResponse<ReminderResponse>(res);
}

export interface TopicSuggestionResponse {
  topics: { topic: string; score: number }[];
  resources: Array<Record<string, unknown>>;
  practice: Array<Record<string, unknown>>;
}

export interface StudyPackResource {
  type: string;
  title: string;
  url: string;
  why: string;
}

export interface StudyPackPractice {
  prompt: string;
  solution_url?: string | null;
  topic?: string;
}

export interface StudyPackResponse {
  taskId: string;
  topic: string;
  resources: StudyPackResource[];
  practice: StudyPackPractice[];
  brief_speech: string;
  cta: string;
  created_at: string;
}

export async function suggestTopics(params: { title: string; notes?: string }): Promise<TopicSuggestionResponse> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/topics/suggest`, origin);
  url.searchParams.set("title", params.title);
  if (params.notes) {
    url.searchParams.set("notes", params.notes);
  }
  const res = await fetch(url.toString());
  return handleResponse<TopicSuggestionResponse>(res);
}

export async function getVapidPublicKey(): Promise<{ publicKey: string }> {
  const res = await fetch(`${API_BASE}/push/vapid-public-key`);
  return handleResponse<{ publicKey: string }>(res);
}

export async function registerPushSubscription(payload: Record<string, unknown>): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/push/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ ok: boolean }>(res);
}

export async function importIcsFile(file: File): Promise<{ imported: number; updated: number; skipped: number }> {
  const formData = new FormData();
  formData.append("file", file, file.name || "calendar.ics");
  const res = await fetch(`${API_BASE}/import/ics-file`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<{ imported: number; updated: number; skipped: number }>(res);
}

export async function getStudyPack(taskId: string): Promise<StudyPackResponse | null> {
  const res = await fetch(`${API_BASE}/study-pack/${encodeURIComponent(taskId)}`);
  if (res.status === 404) {
    return null;
  }
  return handleResponse<StudyPackResponse>(res);
}

export async function buildStudyPack(taskId: string): Promise<StudyPackResponse> {
  const res = await fetch(`${API_BASE}/study-pack/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ taskId, persona: "teacher", escalation: "calm" }),
  });
  return handleResponse<StudyPackResponse>(res);
}

export async function saveMoodleUrl(params: { userId: string; url: string }): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/integrations/moodle/save-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: params.userId, url: params.url }),
  });
  return handleResponse<{ ok: boolean }>(res);
}

export async function refreshMoodleFeed(userId: string): Promise<{ imported: number; updated: number; skipped: number }> {
  const endpoint = `${API_BASE}/integrations/moodle/refresh-now`;
  const requestUrl = `${endpoint}?user_id=${encodeURIComponent(userId)}`;
  const res = await fetch(requestUrl, { method: "POST" });
  return handleResponse<{ imported: number; updated: number; skipped: number }>(res);
}

export async function getMoodleFeedStatus(userId: string): Promise<{
  hasFeed: boolean;
  lastFetchAt: string | null;
  expiresAt: string | null;
  needsRenewal: boolean;
}> {
  const endpoint = `${API_BASE}/integrations/moodle/has-feed`;
  const requestUrl = `${endpoint}?user_id=${encodeURIComponent(userId)}`;
  const res = await fetch(requestUrl);
  return handleResponse<{ hasFeed: boolean; lastFetchAt: string | null }>(res);
}

export type MemoryNext = {
  memory_id: string;
  concept: string;
  due_at: string;
};

export type GradeValue = 2 | 3 | 4 | 5;

export type ReviewOut = {
  next_due_at: string;
  xp_awarded: number;
  persona_msg: string;
};

export async function getNextReviews(user_id: string, limit = 10): Promise<MemoryNext[]> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/memory/next`, origin);
  url.searchParams.set("user_id", user_id);
  url.searchParams.set("limit", limit.toString());
  const res = await fetch(url.toString());
  return handleResponse<MemoryNext[]>(res);
}

export async function postReview(payload: {
  user_id: string;
  memory_id: string;
  grade: GradeValue;
}): Promise<ReviewOut> {
  const res = await fetch(`${API_BASE}/memory/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<ReviewOut>(res);
}

export type ExerciseListItem = {
  id: string;
  concept: string;
  type: "MCQ" | "NUMERIC" | "SHORT";
  difficulty: number;
  tags?: string[];
};

export type ExerciseListResponse = {
  items: ExerciseListItem[];
  page: number;
  page_size: number;
  total: number;
};

export async function listExercises(params: {
  user_id: string;
  search?: string;
  type?: string;
  difficultyMin?: number;
  difficultyMax?: number;
}): Promise<ExerciseListItem[]> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/ex/list`, origin);
  url.searchParams.set("user_id", params.user_id);
  if (params.search) url.searchParams.set("search", params.search);
  if (params.type) url.searchParams.set("type", params.type);
  if (typeof params.difficultyMin === "number") {
    url.searchParams.set("difficulty_min", params.difficultyMin.toString());
  }
  if (typeof params.difficultyMax === "number") {
    url.searchParams.set("difficulty_max", params.difficultyMax.toString());
  }
  const res = await fetch(url.toString());
  const data = await handleResponse<ExerciseListResponse>(res);
  return data.items ?? [];
}

export type ExerciseGetOut = {
  id: string;
  concept: string;
  type: "MCQ" | "NUMERIC" | "SHORT";
  difficulty: number;
  prompt: string;
  choices?: { id: string; text: string }[];
  unit_hint?: string;
  hint?: string;
  max_xp: number;
};

export type ExerciseSubmitIn = {
  user_id: string;
  exercise_id: string;
  answer: Record<string, unknown>;
};

export type MasteryChange = {
  skill_id: string;
  skill_name: string;
  old: number;
  new: number;
  delta: number;
};

export type ExerciseSubmitOut = {
  correct: boolean;
  xp_awarded: number;
  detector_subtype?: "unit" | "sign" | "rounding" | "near_miss";
  explanation?: string;
  related_exercise_id?: string;
  persona_msg?: string;
  mastery_changes?: MasteryChange[];
  persona_reaction?: PersonaReaction;
};

export async function getExercise(user_id: string, id: string): Promise<ExerciseGetOut> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/ex/get`, origin);
  url.searchParams.set("id", id);
  url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString());
  return handleResponse<ExerciseGetOut>(res);
}

export async function submitExercise(payload: ExerciseSubmitIn): Promise<ExerciseSubmitOut> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/ex/submit`, origin);
  url.searchParams.set("id", payload.exercise_id);
  url.searchParams.set("user_id", payload.user_id);
  const res = await fetch(url.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload.answer),
  });
  return handleResponse<ExerciseSubmitOut>(res);
}

export type PersonaReaction = {
  persona: string;
  intensity: string;
  mood: string;
  message: string;
  tags?: string[];
};

export type PersonaProfile = {
  user_id: string;
  persona: string;
  available_personas: string[];
};

export async function getPersonaProfile(user_id: string): Promise<PersonaProfile> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/users/persona`, origin);
  url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString());
  return handleResponse<PersonaProfile>(res);
}

export async function updatePersonaProfile(params: { user_id: string; persona: string }): Promise<PersonaProfile> {
  const res = await fetch(`${API_BASE}/users/persona`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: params.user_id, persona: params.persona }),
  });
  return handleResponse<PersonaProfile>(res);
}

export type BehaviorProfile = {
  engagement_level: number;
  consistency_score: number;
  challenge_preference: number;
  review_vs_new_bias: number;
  session_length_preference: number;
  fatigue_risk: number;
  suggested_length: number;
};

export async function getBehaviorProfile(user_id: string): Promise<BehaviorProfile> {
  const res = await fetch(`${API_BASE}/behavior/profile`, {
    headers: { "X-User-Id": user_id },
  });
  return handleResponse<BehaviorProfile>(res);
}

export type PracticeSessionPayload = {
  user_id: string;
  skill_id?: string | null;
  length: number;
  correct_count: number;
  incorrect_count: number;
  avg_difficulty: number;
  fraction_review: number;
  started_at?: string;
  finished_at?: string;
  abandoned?: boolean;
};

export async function logPracticeSession(payload: PracticeSessionPayload): Promise<void> {
  const res = await fetch(`${API_BASE}/behavior/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await handleResponse<{ status: string; suggested_length: string }>(res);
}

export type SkillMastery = {
  skill_id: string;
  skill_name: string;
  mastery: number;
  updated_at?: string | null;
};

export async function listUserMastery(user_id: string): Promise<SkillMastery[]> {
  const res = await fetch(`${API_BASE}/mastery`, {
    headers: { "X-User-Id": user_id },
  });
  return handleResponse<SkillMastery[]>(res);
}

export type MemoryStats = {
  user_id: string;
  today_reviewed: number;
  daily_cap: number;
  streak_days: number;
  due_count: number;
  exercises_correct_today: number;
  exercises_incorrect_today: number;
  suggested_new_exercises: number;
};

export async function getMemoryStats(user_id: string): Promise<MemoryStats> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/memory/stats`, origin);
  url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString());
  return handleResponse<MemoryStats>(res);
}

export type MicroQuestPlanItem = {
  order: number;
  exercise_id: string;
  concept: string;
  difficulty: number;
  difficulty_label: string;
  is_review: boolean;
  skill_id: string;
  skill_name: string;
  source: "review" | "challenge";
};

export type MicroQuestPlanResponse = {
  user_id: string;
  skill_id: string;
  skill_name: string;
  mastery: number;
  correct_rate: number;
  target_difficulty_low: number;
  target_difficulty_high: number;
  review_count: number;
  challenge_count: number;
  suggested_length: number;
  items: MicroQuestPlanItem[];
};

export async function planMicroQuest(params: {
  user_id: string;
  length?: number;
  skill_id?: string | null;
}): Promise<MicroQuestPlanResponse> {
  const res = await fetch(`${API_BASE}/ex/micro-quest/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: params.user_id,
      length: params.length ?? null,
      skill_id: params.skill_id ?? null,
    }),
  });
  return handleResponse<MicroQuestPlanResponse>(res);
}

export type MicroQuestExercise = {
  exercise_id: string;
  prompt: string;
  concept?: string;
  type: "MCQ" | "NUMERIC" | "SHORT";
  choices?: { id: string | number; text: string }[];
  unit_hint?: string | null;
  difficulty?: number;
  difficulty_label?: string | null;
  is_review?: boolean;
  metadata?: Record<string, unknown>;
};

export type MicroQuestState = {
  id: string;
  skill_id: string;
  skill_name?: string | null;
  length?: number;
  current_index: number;
  total_exercises: number;
  current_exercise: MicroQuestExercise | null;
};

export type MicroQuestCreateResponse = {
  id: string;
  skill_id?: string;
  skill_name?: string;
  length?: number;
};

export async function createMicroQuest(params: {
  user_id: string;
  skill_id?: string | null;
  length: number;
  difficulty_tilt?: "review" | "challenge" | "balanced";
}): Promise<MicroQuestCreateResponse> {
  const res = await fetch(`${API_BASE}/micro-quests`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-User-Id": params.user_id },
    body: JSON.stringify({
      user_id: params.user_id,
      skill_id: params.skill_id ?? null,
      length: params.length,
      difficulty_tilt: params.difficulty_tilt,
    }),
  });
  return handleResponse<MicroQuestCreateResponse>(res);
}

export async function getMicroQuestState(id: string, user_id?: string): Promise<MicroQuestState> {
  const url = new URL(`${API_BASE}/micro-quests/${id}`, typeof window !== "undefined" ? window.location.origin : "http://localhost:5173");
  if (user_id) url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString(), {
    headers: user_id ? { "X-User-Id": user_id } : undefined,
  });
  return handleResponse<MicroQuestState>(res);
}

export type MicroQuestAnswerResponse = {
  correct: boolean;
  persona_reaction?: PersonaReaction | null;
  mastery_changes?: MasteryChange[];
  xp_delta?: number;
  mastery_after?: number;
  streak_after?: number;
  finished?: boolean;
  next_exercise?: MicroQuestExercise | null;
  next_index?: number;
  total_exercises?: number;
};

export async function submitMicroQuestAnswer(params: {
  micro_quest_id: string;
  exercise_id: string;
  answer: Record<string, unknown>;
  user_id: string;
}): Promise<MicroQuestAnswerResponse> {
  const res = await fetch(`${API_BASE}/micro-quests/${params.micro_quest_id}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-User-Id": params.user_id },
    body: JSON.stringify({
      exercise_id: params.exercise_id,
      answer: params.answer,
    }),
  });
  return handleResponse<MicroQuestAnswerResponse>(res);
}

export type MicroQuestSummaryOut = {
  total_exercises: number;
  correct_count: number;
  incorrect_count: number;
  xp_gained: number;
  streak_before?: number;
  streak_after?: number;
  mastery_changes: MasteryChange[];
  skill_id?: string;
  skill_name?: string;
  length?: number;
};

export async function getMicroQuestSummary(id: string, user_id?: string): Promise<MicroQuestSummaryOut> {
  const url = new URL(`${API_BASE}/micro-quests/${id}/summary`, typeof window !== "undefined" ? window.location.origin : "http://localhost:5173");
  if (user_id) url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString(), {
    headers: user_id ? { "X-User-Id": user_id } : undefined,
  });
  return handleResponse<MicroQuestSummaryOut>(res);
}

export type TodayItem =
  | {
      kind: "review_due";
      id: string;
      label: string;
      memory_id: string;
    }
  | {
      kind: "study_block";
      id: string;
      label: string;
      block_id: string;
      duration_minutes: number;
      course_name?: string;
    };

export type TodayAgendaOut = {
  items: TodayItem[];
  persona_line?: string;
};

export async function getTodayAgenda(params: {
  user_id: string;
  exam_id: string;
}): Promise<TodayAgendaOut> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/exam/${params.exam_id}/today`, origin);
  url.searchParams.set("user_id", params.user_id);
  const res = await fetch(url.toString());
  return handleResponse<TodayAgendaOut>(res);
}

export async function postBlockDone(params: {
  user_id: string;
  exam_id: string;
  block_id: string;
}) {
  const res = await fetch(`${API_BASE}/exam/${params.exam_id}/block/${params.block_id}/done`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: params.user_id }),
  });
  return handleResponse(res);
}

export async function postBlockSkip(params: {
  user_id: string;
  exam_id: string;
  block_id: string;
}) {
  const res = await fetch(`${API_BASE}/exam/${params.exam_id}/block/${params.block_id}/skip`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: params.user_id }),
  });
  return handleResponse(res);
}

export type PersonaOut = {
  name?: string;
  warmup_line?: string;
  short_line?: string;
  copy?: string;
};

export async function getPersona(user_id: string): Promise<PersonaOut> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/memory/persona`, origin);
  url.searchParams.set("user_id", user_id);
  const res = await fetch(url.toString());
  return handleResponse<PersonaOut>(res);
}

export type ExamOverview = {
  id: string;
  title: string;
  exam_date: string;
  course_name?: string;
  total_blocks: number;
  remaining_blocks: number;
  days_left: number;
  questionnaire_answer?: number;
};

export type DayBlock = {
  id: string;
  label: string;
  duration_minutes: number;
  type: "study" | "mock_exam";
  completed: boolean;
};

export type DayPlan = {
  date: string;
  blocks: DayBlock[];
};

export async function getExamOverview(params: {
  user_id: string;
  exam_id: string;
}): Promise<ExamOverview> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/exam/${params.exam_id}`, origin);
  url.searchParams.set("user_id", params.user_id);
  const res = await fetch(url.toString());
  return handleResponse<ExamOverview>(res);
}

export async function getExamDayPlan(params: {
  user_id: string;
  exam_id: string;
  date: string;
}): Promise<DayPlan> {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:5173";
  const url = new URL(`${API_BASE}/exam/${params.exam_id}/day`, origin);
  url.searchParams.set("user_id", params.user_id);
  url.searchParams.set("date", params.date);
  const res = await fetch(url.toString());
  return handleResponse<DayPlan>(res);
}

export async function postExamRegenerate(params: {
  user_id: string;
  exam_id: string;
  intensity?: number;
}) {
  const res = await fetch(`${API_BASE}/exam/${params.exam_id}/regenerate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: params.user_id,
      intensity: params.intensity,
    }),
  });
  return handleResponse(res);
}

export const api = {
  getTasks,
  markTaskDone,
  undoTask,
  nextReminder,
  suggestTopics,
  getVapidPublicKey,
  registerPushSubscription,
  importIcsFile,
  getStudyPack,
  buildStudyPack,
  saveMoodleUrl,
  refreshMoodleFeed,
  getMoodleFeedStatus,
  getNextReviews,
  postReview,
  listExercises,
  getExercise,
  submitExercise,
  getTodayAgenda,
  postBlockDone,
  postBlockSkip,
  getPersona,
  getExamOverview,
  getExamDayPlan,
  postExamRegenerate,
};

export default api;
