import { useEffect, useState } from "react";
import { getClientUserId } from "@/lib/user";
import { apiFetch, getAuthToken } from "@/api";

interface StudyProfile {
  goals?: string | null;
  availability?: string | null;
  weak_areas?: string | null;
  preferences?: string | null;
  raw_json?: Record<string, unknown> | null;
  has_profile: boolean;
}

export default function Profile() {
  const [profile, setProfile] = useState<StudyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const token = getAuthToken();
        if (import.meta.env.DEV) {
          console.debug("[profile] requesting /onboarding/profile", { tokenPresent: Boolean(token) });
        }
        const data = await apiFetch<StudyProfile>("/onboarding/profile");
        setProfile(data ?? null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const renderField = (label: string, value?: string | null) => (
    <div className="flex flex-col">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value || "Not set"}</span>
    </div>
  );

  return (
    <div className="space-y-4">
      {loading && <p className="text-sm text-muted-foreground">Loading profile…</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}
      {!loading && profile && !profile.has_profile && !error && (
        <div className="rounded-lg border bg-muted/20 p-4">
          <h2 className="text-lg font-semibold">Study Profile</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            You haven&apos;t set up your study profile yet. Add your goals and availability to personalize Teski.
          </p>
          <button className="mt-3 rounded-md border px-3 py-2 text-sm" type="button">
            Set up my study profile
          </button>
        </div>
      )}

      {!loading && profile && profile.has_profile && (
        <div className="grid gap-4 rounded-lg border p-4 sm:grid-cols-2">
          {renderField("Goals", profile.goals)}
          {renderField("Availability", profile.availability)}
          {renderField("Weak areas", profile.weak_areas)}
          {renderField("Preferences", profile.preferences)}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button className="rounded-md border px-3 py-2 text-sm" type="button">
          Review onboarding questions
        </button>
        <button className="rounded-md border px-3 py-2 text-sm" type="button">
          Edit preferences
        </button>
      </div>
    </div>
  );
}
