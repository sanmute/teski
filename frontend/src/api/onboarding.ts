import { apiFetch } from "./client";
import { DEMO_MODE } from "@/config/demo";
import { getDemoProfile } from "@/demo/state";

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
  if (DEMO_MODE) {
    return Promise.resolve({ ok: true, onboarded: true });
  }
  return apiFetch<OnboardingStatus>("/onboarding/status", { method: "GET" }, { auth: true });
}

export function submitOnboarding(answers: OnboardingAnswers) {
  if (DEMO_MODE) {
    return Promise.resolve({ ok: true, onboarded: true });
  }
  return apiFetch<{ ok: boolean; onboarded: boolean }>("/onboarding/submit", { method: "POST", body: answers }, { auth: true });
}

export function getOnboardingAnswers() {
  if (DEMO_MODE) {
    const profile = getDemoProfile();
    return Promise.resolve({ ok: true, onboarded: true, answers: profile.onboardingAnswers ?? {}, skipped: false });
  }
  return apiFetch<{ ok: boolean; onboarded: boolean; answers: Record<string, unknown> | null; skipped: boolean }>(
    "/onboarding/me",
    { method: "GET" },
    { auth: true },
  );
}
