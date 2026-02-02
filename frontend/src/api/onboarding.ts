import { api, getAuthToken } from "./client";

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
  return api.get<OnboardingStatus>("/onboarding/status");
}

export function submitOnboarding(answers: OnboardingAnswers) {
  return api.post<{ ok: boolean; onboarded: boolean }>("/onboarding/submit", answers);
}

export function getOnboardingAnswers() {
  return api.get<{ ok: boolean; onboarded: boolean; answers: Record<string, unknown> | null; skipped: boolean }>(
    "/onboarding/me",
    {
      headers: { Authorization: `Bearer ${getAuthToken() ?? ""}` },
    },
  );
}
