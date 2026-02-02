import { apiFetch } from "./client";

export type OnboardingStatus = { ok: boolean; onboarded: boolean };

export type OnboardingAnswers = {
  motivation_style: "mentor" | "coach" | "mixed";
  difficulty_preference: "gentle" | "balanced" | "hard";
  daily_minutes_target: number;
  preferred_study_time: "morning" | "afternoon" | "evening" | "varies";
  focus_domains: string[];
  notifications_opt_in: boolean;
  language?: "en" | "fi" | "sv";
  skipped?: boolean;
};

export function getOnboardingStatus() {
  return apiFetch<OnboardingStatus>("/onboarding/status", { method: "GET" }, { auth: true });
}

export function submitOnboarding(answers: OnboardingAnswers) {
  return apiFetch<{ ok: boolean; onboarded: boolean }>("/onboarding/submit", { method: "POST", body: answers }, { auth: true });
}

export function getOnboardingAnswers() {
  return apiFetch<{ ok: boolean; onboarded: boolean; answers: Record<string, unknown> | null; skipped: boolean }>(
    "/onboarding/me",
    { method: "GET" },
    { auth: true },
  );
}
