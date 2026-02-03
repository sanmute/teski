import { DEMO_MODE } from "@/config/demo";
import {
  getDemoTasksSnapshot,
  getDemoExercisesList,
  submitDemoExerciseAnswer,
  getDemoReviewQueue,
  getDemoStats,
  getDemoProfile,
  updateDemoProfile,
} from "@/demo/state";
import { Task } from "@/types/tasks";
import { SummaryMetrics, DailySeries, CourseBreakdown, InsightList } from "@/types/analytics";
import { getClientUserId } from "@/lib/user";

let authToken: string | null = null;

const DEFAULT_BASE_URL = import.meta.env.DEV ? "http://localhost:8000" : "https://teski-zj2gsg.fly.dev";
const rawBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env as Record<string, unknown>).VITE_API_BASE ??
  DEFAULT_BASE_URL;

function normalizeBaseUrl(url: string): string {
  const trimmed = (url || "").trim().replace(/\/+$/, "");
  if (!trimmed) return DEFAULT_BASE_URL;
  const hasProtocol = /^https?:\/\//i.test(trimmed);
  const withProtocol = hasProtocol ? trimmed : `https://${trimmed}`;
  return withProtocol;
}

export const API_BASE_URL = normalizeBaseUrl(rawBaseUrl);
export const API_BASE = `${API_BASE_URL}/api`;
const isProd = Boolean(import.meta.env.PROD);

if (typeof window !== "undefined") {
  const configuredBase = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env as Record<string, unknown>).VITE_API_BASE;
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.log("API_BASE_URL:", API_BASE_URL, "(configured:", configuredBase ?? "default", ")");
  }
  if (isProd && !configuredBase && API_BASE_URL === DEFAULT_BASE_URL) {
    console.warn("[api] VITE_API_BASE_URL missing in production; using fallback");
  }
}

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("teski_token", token);
  } else {
    localStorage.removeItem("teski_token");
  }
}

export function loadAuthTokenFromStorage() {
  const token = localStorage.getItem("teski_token");
  authToken = token;
  return token;
}

// For callers that need to read the current token (e.g., to force-attach headers).
export function getAuthToken(): string | null {
  if (authToken) return authToken;
  const stored = typeof localStorage !== "undefined" ? localStorage.getItem("teski_token") : null;
  authToken = stored;
  return stored;
}

function buildApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/")) return `${API_BASE_URL}${path}`;
  return `${API_BASE_URL}/${path}`;
}

function withAuthHeaders(options: RequestInit = {}, requireAuth = false): RequestInit {
  const headers = new Headers(options.headers || {});
  // Pull latest token lazily to avoid stale module-scoped value when page reloads.
  const token = authToken ?? (typeof localStorage !== "undefined" ? localStorage.getItem("teski_token") : null);
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (requireAuth && !headers.has("Authorization")) {
    if (import.meta.env.DEV) {
      console.warn("[apiFetch] missing auth token for protected request", { path: options?.['__path'] ?? "" });
    }
    throw new Error("Missing auth token for protected request");
  }
  return { ...options, headers };
}

function maybeStringifyBody(body: unknown, headers: Headers): BodyInit | undefined {
  if (body === undefined || body === null) return undefined;
  if (
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof Blob ||
    typeof body === "string"
  ) {
    return body as BodyInit;
  }
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return JSON.stringify(body);
}

type ApiFetchConfig = { auth?: boolean };

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}, config: ApiFetchConfig = {}): Promise<T> {
  if (DEMO_MODE) {
    throw new Error("Demo mode: network requests are disabled.");
  }
  const headers = new Headers(init.headers || {});
  const body = maybeStringifyBody(init.body as unknown, headers);
  const requestInit = withAuthHeaders({ ...init, headers, body, __path: path } as RequestInit, config.auth === true);
  if (import.meta.env.DEV) {
    const hasAuth = (requestInit.headers as Headers).has("Authorization");
    const method = (requestInit.method || "GET").toUpperCase();
    const isProtected = /^(\/api)?\/(onboarding|analytics|tasks|study|memory|push|reminders|ex|exercises|feedback)/.test(path);
    console.debug("[apiFetch]", method, path, { hasAuth });
    if (!hasAuth && isProtected) {
      console.warn("[apiFetch] missing Authorization for protected call", { path, method });
    }
  }
  const response = await fetch(buildApiUrl(path), requestInit);
  const text = await response.text();
  const parsed = text ? (() => { try { return JSON.parse(text); } catch { return text as unknown; } })() : undefined;

  if (!response.ok) {
    const reason = parsed && typeof parsed === "object" && "message" in (parsed as Record<string, unknown>)
      ? (parsed as Record<string, unknown>).message
      : text || response.statusText;
    throw new Error(typeof reason === "string" ? reason : response.statusText);
  }

  return parsed as T;
}

type ExerciseListItemLite = {
  id: string;
  concept: string;
  type: "MCQ" | "NUMERIC" | "SHORT";
  difficulty: number;
  tags?: string[];
};

type ExerciseSubmitPayload = {
  user_id: string;
  exercise_id: string;
  answer: Record<string, unknown>;
};

type ExerciseSubmitResult = {
  correct: boolean;
  xp_awarded: number;
  explanation?: string;
  persona_msg?: string;
};

type ReviewItem = {
  memory_id: string;
  concept: string;
  due_at: string;
};

type StatsBundle = {
  summary: SummaryMetrics;
  daily: DailySeries;
  courses: CourseBreakdown;
  insights: InsightList;
  extras?: Record<string, unknown>;
};

type OnboardingProfileShape = {
  goals?: string | null;
  availability?: string | null;
  weak_areas?: string | null;
  preferences?: string | null;
  has_profile: boolean;
};

export async function getUpcomingTasks(userId?: string): Promise<Task[]> {
  if (DEMO_MODE) {
    return getDemoTasksSnapshot().upcoming;
  }
  return apiFetch<Task[]>(`${API_BASE}/tasks/upcoming`, {
    headers: { "X-User-Id": userId ?? getClientUserId() },
  });
}

export async function getExercisesList(params: {
  user_id?: string;
  search?: string;
  type?: string;
  difficultyMin?: number;
  difficultyMax?: number;
}): Promise<ExerciseListItemLite[]> {
  if (DEMO_MODE) {
    return getDemoExercisesList();
  }
  const qs = new URLSearchParams();
  qs.set("user_id", params.user_id ?? getClientUserId());
  if (params.search) qs.set("search", params.search);
  if (params.type) qs.set("type", params.type);
  if (typeof params.difficultyMin === "number") qs.set("difficulty_min", params.difficultyMin.toString());
  if (typeof params.difficultyMax === "number") qs.set("difficulty_max", params.difficultyMax.toString());
  const res = await apiFetch<{ items: ExerciseListItemLite[] }>(`/api/ex/list?${qs.toString()}`);
  return res?.items ?? [];
}

export async function submitExercise(payload: ExerciseSubmitPayload): Promise<ExerciseSubmitResult> {
  if (DEMO_MODE) {
    const result = submitDemoExerciseAnswer(payload.exercise_id, payload.answer);
    return {
      correct: result.correct,
      xp_awarded: result.xp_awarded ?? 0,
      explanation: result.explanation,
      persona_msg: result.persona_msg,
    };
  }
  const url = new URL(`/api/ex/submit`, API_BASE_URL);
  url.searchParams.set("id", payload.exercise_id);
  url.searchParams.set("user_id", payload.user_id ?? getClientUserId());
  return apiFetch<ExerciseSubmitResult>(url.toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload.answer),
  });
}

export async function getReviews(userId?: string): Promise<ReviewItem[]> {
  if (DEMO_MODE) {
    return getDemoReviewQueue();
  }
  const url = new URL(`/api/memory/next`, API_BASE_URL);
  url.searchParams.set("user_id", userId ?? getClientUserId());
  url.searchParams.set("limit", "10");
  return apiFetch<ReviewItem[]>(url.toString());
}

export async function getStats(_userId?: string): Promise<StatsBundle> {
  if (DEMO_MODE) {
    return getDemoStats();
  }
  const [summary, daily, courses, insights] = await Promise.all([
    apiFetch<SummaryMetrics>("/analytics/me/summary"),
    apiFetch<DailySeries>("/analytics/me/daily?days=14"),
    apiFetch<CourseBreakdown>("/analytics/me/by-course?days=7"),
    apiFetch<InsightList>("/analytics/me/insights"),
  ]);
  return { summary, daily, courses, insights };
}

export async function getOnboardingProfile(): Promise<OnboardingProfileShape> {
  if (DEMO_MODE) {
    return getDemoProfile();
  }
  return apiFetch<OnboardingProfileShape>("/onboarding/profile", { method: "GET" }, { auth: true });
}

export async function updateOnboardingProfile(payload: Partial<OnboardingProfileShape>): Promise<OnboardingProfileShape> {
  if (DEMO_MODE) {
    return updateDemoProfile(payload);
  }
  return apiFetch<OnboardingProfileShape>("/onboarding/profile", { method: "POST", body: payload }, { auth: true });
}

export const api = {
  get: <T>(path: string, options: RequestInit = {}) => apiFetch<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    const preparedBody = maybeStringifyBody(body, headers);
    return apiFetch<T>(path, { ...options, method: options.method ?? "POST", headers, body: preparedBody });
  },
};
import { DEMO_MODE } from "@/config/demo";
import { getDemoTasksSnapshot, getDemoExercisesList, submitDemoExerciseAnswer, getDemoReviewQueue, getDemoStats, getDemoProfile, updateDemoProfile, getDemoExerciseById } from "@/demo/state";
import { Task } from "@/types/tasks";
import { SummaryMetrics, DailySeries, CourseBreakdown, InsightList } from "@/types/analytics";
import { getClientUserId } from "@/lib/user";
