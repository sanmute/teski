import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitOnboarding } from "@/api/onboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

const defaultAnswers = {
  motivation_style: "mentor" as const,
  difficulty_preference: "balanced" as const,
  daily_minutes_target: 15,
  preferred_study_time: "varies" as const,
  focus_domains: [] as string[],
  notifications_opt_in: false,
  language: "en" as const,
};

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ ...defaultAnswers });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = (key: keyof typeof form, value: unknown) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (skip = false) => {
    setSubmitting(true);
    setError(null);
    try {
      await submitOnboarding({ ...form, skipped: skip });
      navigate("/today", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save onboarding");
    } finally {
      setSubmitting(false);
    }
  };

  const focusDomainsText = form.focus_domains.join(", ");

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-6 py-10">
      <div>
        <p className="text-sm font-medium uppercase text-muted-foreground">Welcome</p>
        <h1 className="text-3xl font-semibold tracking-tight">Let’s personalize Teski for you</h1>
        <p className="mt-2 text-muted-foreground">
          These quick preferences help tune difficulty, reminders, and study recommendations. You can change them later.
        </p>
      </div>

      <div className="grid gap-6 rounded-2xl border bg-card p-6 shadow-sm">
        <div className="grid gap-2">
          <Label>Motivation style</Label>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {["mentor", "coach", "mixed"].map((style) => (
              <button
                key={style}
                type="button"
                onClick={() => update("motivation_style", style)}
                className={`rounded-lg border px-3 py-2 text-left transition ${
                  form.motivation_style === style ? "border-primary bg-primary/10" : "border-border"
                }`}
              >
                <div className="font-semibold capitalize">{style}</div>
                <div className="text-xs text-muted-foreground">
                  {style === "mentor"
                    ? "Guidance plus encouragement"
                    : style === "coach"
                    ? "Accountability and clear goals"
                    : "A bit of both"}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label>Difficulty preference</Label>
            <select
              className="rounded-md border border-input bg-background px-3 py-2"
              value={form.difficulty_preference}
              onChange={(e) => update("difficulty_preference", e.target.value)}
            >
              <option value="gentle">Gentle</option>
              <option value="balanced">Balanced</option>
              <option value="hard">Push me</option>
            </select>
          </div>

          <div className="grid gap-2">
            <Label>Daily minutes target</Label>
            <Input
              type="number"
              min={5}
              max={240}
              value={form.daily_minutes_target}
              onChange={(e) => update("daily_minutes_target", Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">Aim for something realistic. You can adjust anytime.</p>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label>Preferred study time</Label>
            <select
              className="rounded-md border border-input bg-background px-3 py-2"
              value={form.preferred_study_time}
              onChange={(e) => update("preferred_study_time", e.target.value)}
            >
              <option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option>
              <option value="evening">Evening</option>
              <option value="varies">It varies</option>
            </select>
          </div>

          <div className="grid gap-2">
            <Label>Focus domains (comma separated)</Label>
            <Textarea
              rows={2}
              placeholder="e.g. python, math, writing"
              value={focusDomainsText}
              onChange={(e) =>
                update(
                  "focus_domains",
                  e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean)
                )
              }
            />
          </div>
        </div>

        <div className="flex items-center justify-between rounded-lg border px-3 py-2">
          <div className="space-y-1">
            <Label>Reminders & notifications</Label>
            <p className="text-xs text-muted-foreground">Allow gentle nudges about streaks and upcoming work.</p>
          </div>
          <Switch checked={form.notifications_opt_in} onCheckedChange={(v) => update("notifications_opt_in", v)} />
        </div>
      </div>

      {error && <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

      <div className="flex flex-wrap gap-3">
        <Button disabled={submitting} onClick={() => handleSubmit(false)}>
          {submitting ? "Saving..." : "Save and continue"}
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => handleSubmit(true)}>
          Skip for now
        </Button>
      </div>
    </div>
  );
}
