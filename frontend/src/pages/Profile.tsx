import { useEffect, useState } from "react";
import { getOnboardingProfile, updateOnboardingProfile } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/sonner";
import { DEMO_MODE } from "@/config/demo";

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
  const [draft, setDraft] = useState<Partial<StudyProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getOnboardingProfile();
        setProfile(data ?? null);
        setDraft({
          goals: data?.goals ?? "",
          availability: data?.availability ?? "",
          weak_areas: data?.weak_areas ?? "",
          preferences: data?.preferences ?? "",
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSave = async () => {
    try {
      const updated = await updateOnboardingProfile(draft);
      setProfile(updated);
      toast.success(DEMO_MODE ? "Saved (demo)" : "Preferences saved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save profile");
    }
  };

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
        <div className="grid gap-4 rounded-lg border p-4">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Goals</label>
            <Textarea
              value={draft.goals ?? ""}
              onChange={(e) => setDraft((prev) => ({ ...prev, goals: e.target.value }))}
              placeholder="e.g., Ace Circuits II midterm"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Availability</label>
            <Input
              value={draft.availability ?? ""}
              onChange={(e) => setDraft((prev) => ({ ...prev, availability: e.target.value }))}
              placeholder="Mon–Thu evenings"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Weak areas</label>
            <Textarea
              value={draft.weak_areas ?? ""}
              onChange={(e) => setDraft((prev) => ({ ...prev, weak_areas: e.target.value }))}
              placeholder="Topics you want Teski to emphasize"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Preferences</label>
            <Textarea
              value={draft.preferences ?? ""}
              onChange={(e) => setDraft((prev) => ({ ...prev, preferences: e.target.value }))}
              placeholder="Block length, study buddy, reminders…"
            />
          </div>
          <div className="flex justify-end">
            <Button size="sm" onClick={handleSave}>
              Save {DEMO_MODE ? "(demo)" : ""}
            </Button>
          </div>
        </div>
      )}

    </div>
  );
}
