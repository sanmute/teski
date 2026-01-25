import { useEffect, useState } from "react";
import { getClientUserId } from "@/lib/user";
import { apiFetch } from "@/api";

interface LearnerProfile {
  explanation_style?: string | null;
  practice_style?: string | null;
  focus_time?: string | null;
  communication_style?: string | null;
  challenges?: string[] | null;
  proactivity_level?: string | null;
  semester_goal?: string | null;
}

export default function Profile() {
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch<{ profile?: LearnerProfile }>(`/onboarding/profile`, {
          headers: { "X-User-Id": getClientUserId() },
        });
        if (data?.profile) {
          setProfile(data.profile);
        } else {
          setProfile(null);
        }
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
      {!loading && !profile && !error && (
        <p className="text-sm text-muted-foreground">
          You haven&apos;t completed onboarding yet. When you do, your study profile will appear here.
        </p>
      )}

      {profile && (
        <div className="grid gap-4 rounded-lg border p-4 sm:grid-cols-2">
          {renderField("Explanation style", profile.explanation_style)}
          {renderField("Practice style", profile.practice_style)}
          {renderField("Focus time", profile.focus_time)}
          {renderField("Communication style", profile.communication_style)}
          {renderField("Proactivity level", profile.proactivity_level)}
          {renderField("Semester goal", profile.semester_goal)}
          <div className="sm:col-span-2">
            <span className="text-xs uppercase tracking-wide text-muted-foreground">Challenges</span>
            <div className="mt-1 flex flex-wrap gap-2">
              {(profile.challenges ?? []).length > 0 ? (
                profile.challenges!.map((challenge) => (
                  <span
                    key={challenge}
                    className="rounded-full border px-3 py-1 text-xs text-muted-foreground"
                  >
                    {challenge}
                  </span>
                ))
              ) : (
                <span className="text-sm">No challenges selected</span>
              )}
            </div>
          </div>
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
