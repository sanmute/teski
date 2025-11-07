export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

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
  const endpoint = `${API_BASE}/integrations/moodle/save-url`;
  const requestUrl = `${endpoint}?user_id=${encodeURIComponent(params.userId)}&url=${encodeURIComponent(params.url)}`;
  const res = await fetch(requestUrl, { method: "POST" });
  return handleResponse<{ ok: boolean }>(res);
}

export async function refreshMoodleFeed(userId: string): Promise<{ imported: number; updated: number; skipped: number }> {
  const endpoint = `${API_BASE}/integrations/moodle/refresh-now`;
  const requestUrl = `${endpoint}?user_id=${encodeURIComponent(userId)}`;
  const res = await fetch(requestUrl, { method: "POST" });
  return handleResponse<{ imported: number; updated: number; skipped: number }>(res);
}

export async function getMoodleFeedStatus(userId: string): Promise<{ hasFeed: boolean; lastFetchAt: string | null }> {
  const endpoint = `${API_BASE}/integrations/moodle/has-feed`;
  const requestUrl = `${endpoint}?user_id=${encodeURIComponent(userId)}`;
  const res = await fetch(requestUrl);
  return handleResponse<{ hasFeed: boolean; lastFetchAt: string | null }>(res);
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
};

export default api;
