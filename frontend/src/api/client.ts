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

export const api = {
  get: <T>(path: string, options: RequestInit = {}) => apiFetch<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    const preparedBody = maybeStringifyBody(body, headers);
    return apiFetch<T>(path, { ...options, method: options.method ?? "POST", headers, body: preparedBody });
  },
};
