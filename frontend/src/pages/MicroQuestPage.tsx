import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { PersonaReactionBubble } from "@/components/PersonaReactionBubble";
import { MicroQuestSummary } from "@/components/micro-quest/MicroQuestSummary";
import { toast } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";
import { getClientUserId } from "@/lib/user";
import {
  createMicroQuest,
  getBehaviorProfile,
  getMicroQuestState,
  submitMicroQuestAnswer,
  getMicroQuestSummary,
  type BehaviorProfile,
  type MicroQuestAnswerResponse,
  type MicroQuestExercise,
  type MicroQuestState,
  type MicroQuestSummaryOut,
  type MasteryChange,
} from "@/api";
import {
  getMicroQuestTodayCount,
  getMicroQuestWeeklyCount,
  recordMicroQuestRun,
} from "@/lib/microQuestProgress";

const DEFAULT_LENGTH = 5;

const clampLength = (len: number | undefined) => Math.min(7, Math.max(3, Math.round(len ?? DEFAULT_LENGTH)));

export default function MicroQuestPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const { microQuestId: routeQuestId } = useParams();
  const [searchParams] = useSearchParams();

  const [questId, setQuestId] = useState<string | null>(routeQuestId ?? null);
  const [questState, setQuestState] = useState<MicroQuestState | null>(null);
  const [behavior, setBehavior] = useState<BehaviorProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(!!routeQuestId);
  const [, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answerInput, setAnswerInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<MicroQuestAnswerResponse | null>(null);
  const [latestReaction, setLatestReaction] = useState<MicroQuestAnswerResponse["persona_reaction"]>(null);
  const [latestMastery, setLatestMastery] = useState<MasteryChange[]>([]);
  const [pendingNext, setPendingNext] = useState<{ exercise: MicroQuestExercise; index: number; total?: number } | null>(null);
  const [summary, setSummary] = useState<MicroQuestSummaryOut | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [todayRuns, setTodayRuns] = useState(() => getMicroQuestTodayCount());
  const [weekRuns, setWeekRuns] = useState(() => getMicroQuestWeeklyCount());

  const finishTimer = useRef<number | null>(null);

  useEffect(() => {
    getBehaviorProfile(userId)
      .then(setBehavior)
      .catch(() => setBehavior(null));
  }, [userId]);

  useEffect(() => {
    if (!questId && routeQuestId) {
      setQuestId(routeQuestId);
    }
  }, [questId, routeQuestId]);

  const defaultLengthFromBehavior = useCallback(() => {
    if (!behavior) return DEFAULT_LENGTH;
    if (behavior.fatigue_risk >= 75) return 3;
    if (behavior.challenge_preference >= 75) return 7;
    return behavior.suggested_length ?? behavior.session_length_preference ?? DEFAULT_LENGTH;
  }, [behavior]);

  const loadQuestState = useCallback(
    async (id: string) => {
      setLoading(true);
      setError(null);
      setSubmitError(null);
      setFeedback(null);
      setPendingNext(null);
      try {
        const data = await getMicroQuestState(id, userId);
        setQuestState(data);
        setAnswerInput("");
      } catch (err) {
        console.error(err);
        setError("Could not load this micro-quest. Please retry.");
      } finally {
        setLoading(false);
      }
    },
    [userId],
  );

  const finalizeQuest = useCallback(
    async (id: string) => {
      if (finishTimer.current) {
        window.clearTimeout(finishTimer.current);
        finishTimer.current = null;
      }
      setSummaryLoading(true);
      try {
        const summaryData = await getMicroQuestSummary(id, userId);
        setSummary(summaryData);
        recordMicroQuestRun();
        setTodayRuns(getMicroQuestTodayCount());
        setWeekRuns(getMicroQuestWeeklyCount());
        setQuestState(null);
      } catch (err) {
        console.error(err);
        setError("Finished the run, but couldn't load the summary.");
      } finally {
        setSummaryLoading(false);
      }
    },
    [userId],
  );

  const startNewQuest = useCallback(
    async (opts?: { skillId?: string | null; length?: number }) => {
      const desiredLength = clampLength(opts?.length ?? defaultLengthFromBehavior());
      setStarting(true);
      setError(null);
      setSummary(null);
      setSubmitError(null);
      setFeedback(null);
      setPendingNext(null);
      try {
        const quest = await createMicroQuest({
          user_id: userId,
          skill_id: opts?.skillId ?? undefined,
          length: desiredLength,
          difficulty_tilt: behavior && behavior.challenge_preference >= 70 ? "challenge" : undefined,
        });
        setQuestId(quest.id);
        navigate(`/practice/micro-quest/${quest.id}`, { replace: true });
        await loadQuestState(quest.id);
      } catch (err) {
        console.error(err);
        setError("Couldn't start a run. Please try again.");
        toast.error("Couldn't start a run. Please try again.");
      } finally {
        setStarting(false);
      }
    },
    [behavior, defaultLengthFromBehavior, loadQuestState, navigate, userId],
  );

  const startFromSearch = useCallback(() => {
    const skillId = searchParams.get("skill_id");
    const len = Number(searchParams.get("len")) || defaultLengthFromBehavior();
    startNewQuest({ skillId, length: len });
  }, [defaultLengthFromBehavior, searchParams, startNewQuest]);

  useEffect(() => {
    if (questId) {
      loadQuestState(questId);
      return () => {
        if (finishTimer.current) {
          window.clearTimeout(finishTimer.current);
          finishTimer.current = null;
        }
      };
    }
    startFromSearch();

    return () => {
      if (finishTimer.current) {
        window.clearTimeout(finishTimer.current);
        finishTimer.current = null;
      }
    };
  }, [loadQuestState, questId, startFromSearch]);

  const currentExercise = questState?.current_exercise ?? null;
  const progressPercent = questState ? ((questState.current_index + 1) / Math.max(questState.total_exercises, 1)) * 100 : 0;

  const handleSubmit = async () => {
    if (!questId || !currentExercise || submitting || feedback) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload = buildAnswerPayload(currentExercise, answerInput);
      const response = await submitMicroQuestAnswer({
        micro_quest_id: questId,
        exercise_id: currentExercise.exercise_id,
        answer: payload,
        user_id: userId,
      });
      setFeedback(response);
      setLatestReaction(response.persona_reaction ?? null);
      setLatestMastery(response.mastery_changes ?? []);
      if (response.finished) {
        finishTimer.current = window.setTimeout(() => finalizeQuest(questId), 800);
      } else if (response.next_exercise) {
        setPendingNext({
          exercise: response.next_exercise,
          index: response.next_index ?? (questState?.current_index ?? 0) + 1,
          total: response.total_exercises,
        });
      }
    } catch (err) {
      console.error(err);
      setSubmitError(err instanceof Error ? err.message : "Could not submit answer. Please retry.");
      toast.error("Could not submit answer. Please retry.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    if (!questId) return;
    if (feedback?.finished) {
      await finalizeQuest(questId);
      return;
    }
    setFeedback(null);
    setSubmitError(null);
    setLatestReaction(null);
    setLatestMastery([]);
    if (pendingNext && questState) {
      setQuestState({
        ...questState,
        current_exercise: pendingNext.exercise,
        current_index: pendingNext.index,
        total_exercises: pendingNext.total ?? questState.total_exercises,
      });
      setPendingNext(null);
      setAnswerInput("");
      return;
    }
    await loadQuestState(questId);
  };

  const handleBack = () => navigate("/today");

  const summaryMessage = buildRunReaction(
    summary ? summary.correct_count / Math.max(summary.total_exercises || 1, 1) : 0,
  );

  const nextLength = chooseNextLength(behavior, summary?.length ?? questState?.total_exercises ?? DEFAULT_LENGTH);

  useEffect(() => {
    return () => {
      if (finishTimer.current) {
        window.clearTimeout(finishTimer.current);
      }
    };
  }, []);

  if (summary) {
    return (
      <div className="mx-auto w-full max-w-4xl pb-16">
        <MicroQuestSummary
          skillId={summary.skill_id}
          skillName={summary.skill_name}
          totalQuestions={summary.total_exercises}
          correctCount={summary.correct_count}
          xpTotal={summary.xp_gained}
          masteryDeltas={summary.mastery_changes ?? []}
          todayRuns={todayRuns}
          weekRuns={weekRuns}
          summaryMessage={summaryMessage}
          runReaction={summaryMessage}
          streakAfter={summary.streak_after}
          onRepeat={() => startNewQuest({ skillId: summary.skill_id, length: nextLength })}
          onBack={handleBack}
          onOpenSkillMap={summary.skill_id ? () => navigate(`/skills?focus=${summary.skill_id}`) : undefined}
          ctaLabel={`Do another ${nextLength}-question run`}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl pb-16">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Micro-quest</h1>
          <p className="text-sm text-slate-500">Short runs that escalate when you're rolling.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={() => navigate("/skills")}>Skill map</Button>
          <Button variant="outline" onClick={handleBack}>
            Back to Today
          </Button>
        </div>
      </div>

      {loading && <QuestSkeleton />}

      {!loading && error && (
        <div className="mx-auto mt-6 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Something went wrong</h2>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
          <div className="mt-4 flex justify-center gap-3">
            <Button variant="outline" onClick={handleBack}>
              Return to Today
            </Button>
            <Button onClick={() => (questId ? loadQuestState(questId) : startFromSearch())}>Retry</Button>
          </div>
        </div>
      )}

      {!loading && !error && questState && currentExercise && (
        <div className="mx-auto mt-6 w-full max-w-3xl space-y-4">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Micro-quest in {questState.skill_name ?? "your focus"}</p>
                <h2 className="text-xl font-semibold text-slate-900">
                  Question {Math.min(questState.current_index + 1, questState.total_exercises)} of {questState.total_exercises}
                </h2>
                <p className="text-sm text-slate-600">
                  {currentExercise.concept ?? ""}
                </p>
              </div>
              <div className="text-right text-xs text-slate-500">
                <p>Run length</p>
                <p className="text-lg font-semibold text-slate-900">{questState.total_exercises}</p>
              </div>
            </div>
            <div className="mt-4">
              <Progress value={progressPercent} className="h-2" />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-800">
                {difficultyLabel(currentExercise)}
              </span>
              {currentExercise.is_review && (
                <span className="rounded-full bg-amber-100 px-3 py-1 font-medium text-amber-800">Review from mistakes</span>
              )}
            </div>

            <div className="mt-5 space-y-3 text-sm text-slate-700">
              <p className="whitespace-pre-line text-base font-medium text-slate-900">{currentExercise.prompt ?? currentExercise.concept ?? ""}</p>
              {renderAnswerField(currentExercise, answerInput, setAnswerInput, submitting || Boolean(feedback))}
              {submitError && <p className="text-xs text-rose-600">{submitError}</p>}
            </div>

            {feedback && (
              <div className="mt-4 rounded-2xl bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">
                  {feedback.correct ? "Marked correct" : "Logged for review"}
                </p>
                {latestMastery.length > 0 && (
                  <div className="mt-2 space-y-1 text-sm text-slate-600">
                    {latestMastery.map((change) => (
                      <div key={change.skill_id} className="flex items-center justify-between">
                        <span>{change.skill_name}</span>
                        <span>
                          {Math.round(change.old)}% {"->"} {Math.round(change.new)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                {feedback.xp_delta !== undefined && (
                  <p className="mt-2 text-xs text-slate-500">XP change: {feedback.xp_delta >= 0 ? "+" : ""}{feedback.xp_delta}</p>
                )}
              </div>
            )}

            <PersonaReactionBubble reaction={latestReaction} className="mt-3" />

            <div className="mt-6 flex flex-wrap items-center justify-end gap-3">
              {feedback && (
                <Button variant="outline" onClick={handleNext}>
                  {feedback.finished ? "See summary" : "Next question"}
                </Button>
              )}
              <Button onClick={handleSubmit} disabled={submitting || Boolean(feedback) || !answerInput.trim()}>
                {submitting ? "Submitting..." : feedback ? "Submitted" : "Submit answer"}
              </Button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <p className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
              <span>Run momentum</span>
              <span>
                {todayRuns} today / {weekRuns} this week
              </span>
            </p>
            <p className="mt-2 text-slate-700">
              {behavior
                ? behavior.fatigue_risk >= 70
                  ? "We're keeping this one short - finish strong and we'll cool down."
                  : behavior.challenge_preference >= 70
                    ? "Challenge preference detected. Escalating difficulty when you're correct."
                    : "Balanced mix of review and stretch based on your profile."
                : "Teski is adapting difficulty as you answer."}
            </p>
          </div>
        </div>
      )}

      {summaryLoading && (
        <div className="mx-auto mt-6 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="text-sm text-slate-600">Wrapping up your run...</p>
          <Skeleton className="mt-3 h-3 w-full" />
        </div>
      )}
    </div>
  );
}

const renderAnswerField = (
  exercise: MicroQuestExercise,
  value: string,
  onChange: (v: string) => void,
  disabled: boolean,
) => {
  if (exercise.type === "MCQ" && exercise.choices) {
    return (
      <div className="space-y-2">
        {exercise.choices.map((choice) => {
          const choiceId = String(choice.id ?? choice.text ?? "");
          const choiceText = choice.text ?? String(choice.id ?? "");
          return (
            <label
              key={choiceId}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2",
                value === choiceId ? "border-slate-900 bg-slate-900/5" : "border-slate-200",
                disabled && "opacity-70",
              )}
            >
              <input
                type="radio"
                name="micro-quest-choice"
                value={choiceId}
                checked={value === choiceId}
                onChange={() => onChange(choiceId)}
                disabled={disabled}
                className="h-4 w-4"
              />
              <span className="text-sm text-slate-700">{choiceText}</span>
            </label>
          );
        })}
      </div>
    );
  }

  if (exercise.type === "NUMERIC") {
    return (
      <div>
        <Input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter numeric answer"
          disabled={disabled}
        />
        {exercise.unit_hint && <p className="mt-1 text-xs text-slate-500">Unit: {exercise.unit_hint}</p>}
      </div>
    );
  }

  return (
    <div>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value.slice(0, 400))}
        rows={4}
        placeholder="Type your answer"
        disabled={disabled}
      />
      <p className="mt-1 text-xs text-slate-500">{value.length} / 400</p>
    </div>
  );
};

const difficultyLabel = (exercise: MicroQuestExercise) => {
  if (exercise.difficulty_label) return exercise.difficulty_label;
  if (exercise.difficulty) return `Difficulty ${exercise.difficulty}/5`;
  return "Adaptive difficulty";
};

const buildAnswerPayload = (exercise: MicroQuestExercise, raw: string) => {
  if (exercise.type === "MCQ") {
    if (!raw) throw new Error("Choose an option");
    const matching = exercise.choices?.find((choice) => String(choice.id ?? choice.text) === raw);
    const numeric = Number(raw);
    const value = !Number.isNaN(numeric) ? numeric : raw;
    return { choice: matching?.id ?? value } as Record<string, unknown>;
  }

  if (exercise.type === "NUMERIC") {
    const trimmed = raw.trim();
    if (!trimmed) throw new Error("Enter a number");
    const value = Number(trimmed);
    if (Number.isNaN(value)) throw new Error("Enter a number");
    return { value };
  }

  const text = raw.trim();
  if (!text) throw new Error("Enter your answer");
  return { text };
};

const buildRunReaction = (ratio: number) => {
  if (ratio >= 0.8) {
    return "Your practice is paying off. You handled most of those questions.";
  }
  if (ratio >= 0.5) {
    return "Solid work. You pushed yourself and cleaned up some weak spots.";
  }
  return "You picked a tough set. These mistakes are now on Teski's radar - we'll come back to them.";
};

const chooseNextLength = (behavior: BehaviorProfile | null, justRan: number) => {
  const base = clampLength(justRan || DEFAULT_LENGTH);
  if (!behavior) return base;
  if (behavior.fatigue_risk >= 70) return Math.min(base, 4);
  if (behavior.challenge_preference >= 70) return Math.min(7, base + 1);
  return clampLength(behavior.suggested_length ?? behavior.session_length_preference ?? base);
};

const QuestSkeleton = () => (
  <div className="mx-auto mt-6 w-full max-w-3xl space-y-3">
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="mt-2 h-7 w-64" />
      <Skeleton className="mt-4 h-2 w-full" />
      <Skeleton className="mt-4 h-20 w-full" />
      <Skeleton className="mt-4 h-10 w-40" />
    </div>
  </div>
);
