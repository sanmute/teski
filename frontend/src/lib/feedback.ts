import { API_BASE_URL } from "@/api/client";

function safeWindow() {
  return typeof window !== "undefined" ? window : undefined;
}

function safeNavigator() {
  return typeof navigator !== "undefined" ? navigator : undefined;
}

function safeDocument() {
  return typeof document !== "undefined" ? document : undefined;
}

export function getAppVersion(): string {
  const env = import.meta.env as Record<string, unknown>;
  const version =
    (env.VITE_APP_VERSION as string | undefined) ||
    (env.VITE_GIT_SHA as string | undefined) ||
    (env.VERCEL_GIT_COMMIT_SHA as string | undefined) ||
    (env.VITE_API_VERSION as string | undefined);
  return version || "(unknown)";
}

export function collectFeedbackContext(
  featureContext?: string,
  extraMetadata: Record<string, unknown> = {},
) {
  const win = safeWindow();
  const nav = safeNavigator();
  const doc = safeDocument();

  const page = win?.location?.href ?? "(unknown)";
  const pagePath = win ? `${win.location.pathname}${win.location.search}${win.location.hash}` : undefined;

  const viewport =
    win && typeof win.innerWidth === "number" && typeof win.innerHeight === "number"
      ? { w: win.innerWidth, h: win.innerHeight, dpr: win.devicePixelRatio || 1 }
      : undefined;

  const metadata = {
    timestamp_iso: new Date().toISOString(),
    user_agent: nav?.userAgent,
    platform: (nav as any)?.userAgentData?.platform || nav?.platform,
    language: nav?.language,
    viewport,
    timezone: typeof Intl !== "undefined" ? Intl.DateTimeFormat().resolvedOptions().timeZone : undefined,
    referrer: doc?.referrer,
    api_base_url: API_BASE_URL,
    feature_context: featureContext,
    page_path: pagePath,
    ...extraMetadata,
  };

  return {
    page,
    app_version: getAppVersion(),
    metadata,
  };
}
