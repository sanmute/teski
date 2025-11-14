import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertCircle, Check, Loader2 } from "lucide-react";

import { fetchStudySession, completeStudySession } from "@/api/study";
import { SessionPlan, StudySessionDetailResponse } from "@/types/study";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { ExplainPanel } from "@/components/ExplainPanel";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { CharacterId, CHARACTER_OPTIONS } from "@/types/characters";
import { getInitialCharacter, useCharacterTheme } from "@/hooks/useCharacterTheme";
import { SessionCompanion } from "@/components/SessionCompanion";

type Phase = "prepare" | "focus" | "close";
type GoalStatus = "yes" | "almost" | "no" | null;
type TimeFeelingState = "too_short" | "just_right" | "too_long" | null;

export default function StudySessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<StudySessionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("prepare");
  const [focusStartedAt, setFocusStartedAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [reflectionGoal, setReflectionGoal] = useState<GoalStatus>(null);
  const [difficulty, setDifficulty] = useState<number | null>(null);
  const [timeFeeling, setTimeFeeling] = useState<TimeFeelingState>(null);
  const [reflectionNotes, setReflectionNotes] = useState("");
  const [explainInput, setExplainInput] = useState("");
  const [explainText, setExplainText] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [activeCharacter, setActiveCharacter] = useState<CharacterId>(() => getInitialCharacter());

  const { toast } = useToast();
  const navigate = useNavigate();
  useCharacterTheme(activeCharacter);

  useEffect(() => {
    const load = async () => {
      if (!sessionId) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchStudySession(Number(sessionId));
        setSession(data);
        if (data.status === "completed") {
          setPhase("close");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load session");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [sessionId]);

  useEffect(() => {
    if (phase !== "focus" || !focusStartedAt) return;
    const interval = setInterval(() => {
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - focusStartedAt) / 1000)));
    }, 1000);
    return () => clearInterval(interval);
  }, [phase, focusStartedAt]);

  const minutesDisplay = useMemo(() => {
    const minutes = Math.floor(elapsedSeconds / 60)
      .toString()
      .padStart(2, "0");
    const seconds = (elapsedSeconds % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
  }, [elapsedSeconds]);
  const elapsedMinutes = Math.floor(elapsedSeconds / 60);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Loading study session…
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-destructive">
        <AlertCircle className="mr-2 h-5 w-5" />
        {error || "Session not found"}
      </div>
    );
  }

  const handleStartFocus = () => {
    setPhase("focus");
    setFocusStartedAt(Date.now());
    setElapsedSeconds(0);
  };

  const handleGoToClose = () => {
    setPhase("close");
    if (focusStartedAt) {
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - focusStartedAt) / 1000)));
    }
  };

  const handleSubmitReflection = async () => {
    if (!session) return;
    setSubmitting(true);
    const actualMinutes = Math.max(1, Math.floor(elapsedSeconds / 60) || session.planned_duration_minutes);
    try {
      await completeStudySession(session.session_id, {
        goal_completed:
          reflectionGoal === "yes" ? true : reflectionGoal === "no" ? false : undefined,
        perceived_difficulty: difficulty ?? undefined,
        time_feeling: timeFeeling ?? undefined,
        notes: reflectionNotes || undefined,
        actual_duration_minutes: actualMinutes,
      });
      toast({
        title: "Session completed",
        description: "Nice work! Keep up the momentum.",
      });
      setSession((prev) =>
        prev
          ? {
              ...prev,
              status: "completed",
              ended_at: new Date().toISOString(),
            }
          : prev
      );
    } catch (err) {
      toast({
        title: "Failed to complete session",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleExplain = () => {
    if (!explainInput.trim()) return;
    setExplainText(explainInput.trim());
  };

  const renderPlan = (plan: SessionPlan, description?: string) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{plan.title}</CardTitle>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </CardHeader>
      <CardContent className="space-y-3">
        {plan.steps.map((step) => (
          <div key={step.id} className="rounded-md border border-dashed p-3">
            <p className="text-sm font-medium">{step.label}</p>
            {step.description && <p className="text-xs text-muted-foreground">{step.description}</p>}
          </div>
        ))}
      </CardContent>
    </Card>
  );

  const renderPrepare = () => (
    <div className="space-y-4">
      {renderPlan(session.plan_prepare)}
      <div className="rounded-lg border p-4">
        <p className="text-sm text-muted-foreground mb-2">
          When you feel ready, start the focused block. You can always return to this plan.
        </p>
        <Button onClick={handleStartFocus}>Start session</Button>
      </div>
    </div>
  );

  const renderFocus = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Timer</CardTitle>
            <p className="text-sm text-muted-foreground">
              Planned: {session.planned_duration_minutes} min
            </p>
          </div>
          <div className="text-3xl font-mono">{minutesDisplay}</div>
        </CardHeader>
      </Card>

      {renderPlan(session.plan_focus)}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Need a different explanation?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Paste text or describe what you're stuck on"
            value={explainInput}
            onChange={(e) => setExplainInput(e.target.value)}
          />
          <Button variant="outline" onClick={handleExplain} disabled={!explainInput.trim()}>
            Explain this
          </Button>
          {explainText && (
            <div className="rounded-md border p-2">
              <ExplainPanel text={explainText} />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleGoToClose}>Go to wrap-up</Button>
      </div>
    </div>
  );

  const renderClose = () => (
    <div className="space-y-4">
      {renderPlan(session.plan_close)}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Reflection</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm font-medium">Did you complete what you planned?</p>
            <div className="mt-2 flex gap-2">
              {[
                { value: "yes", label: "Yes" },
                { value: "almost", label: "Almost" },
                { value: "no", label: "Not really" },
              ].map((opt) => (
                <Button
                  key={opt.value}
                  type="button"
                  variant={reflectionGoal === opt.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setReflectionGoal(opt.value as GoalStatus)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-medium">How hard did this feel?</p>
            <div className="mt-2 flex gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <Button
                  key={value}
                  type="button"
                  variant={difficulty === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setDifficulty(value)}
                >
                  {value}
                </Button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-medium">How did the time feel?</p>
            <div className="mt-2 flex gap-2">
              {[
                { value: "too_short", label: "Too short" },
                { value: "just_right", label: "Just right" },
                { value: "too_long", label: "Too long" },
              ].map((opt) => (
                <Button
                  key={opt.value}
                  type="button"
                  variant={timeFeeling === opt.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTimeFeeling(opt.value as TimeFeelingState)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-sm font-medium">Notes</p>
            <Textarea
              placeholder="Optional reflections…"
              value={reflectionNotes}
              onChange={(e) => setReflectionNotes(e.target.value)}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSubmitReflection} disabled={submitting}>
              {submitting ? "Saving…" : "Complete session"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const phaseContent = phase === "prepare" ? renderPrepare() : phase === "focus" ? renderFocus() : renderClose();

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <header className="rounded-lg border bg-card p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-xl font-semibold">{session.task_title}</h1>
            <p className="text-sm text-muted-foreground">
              {session.course || "Uncategorized"} • {session.block_label} ({session.block_duration_minutes} min)
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {session.status === "completed" && (
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                <Check className="h-3 w-3" />
                Completed
              </span>
            )}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Companion</span>
              <select
                className="rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={activeCharacter}
                onChange={(e) => setActiveCharacter(e.target.value as CharacterId)}
              >
                {CHARACTER_OPTIONS.map((opt) => (
                  <option key={opt.id} value={opt.id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      <div className="flex gap-2 text-sm">
        {["prepare", "focus", "close"].map((name) => (
          <div
            key={name}
            className={cn(
              "flex-1 rounded-md border px-3 py-2 text-center capitalize",
              phase === name ? "border-primary bg-primary/5" : "border-border bg-muted/20"
            )}
          >
            {name}
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="space-y-4">{phaseContent}</div>
        <div className="space-y-4">
          <SessionCompanion phase={phase} elapsedMinutes={elapsedMinutes} character={activeCharacter} />
        </div>
      </div>
    </div>
  );
}
