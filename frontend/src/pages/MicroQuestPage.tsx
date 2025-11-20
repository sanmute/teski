import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ExerciseModal, type ExerciseResult } from "@/components/ExerciseModal";
import {
  planMicroQuest,
  type MicroQuestPlanItem,
  type MicroQuestPlanResponse,
  type MasteryChange,
  type PersonaReaction,
  logPracticeSession,
} from "@/api";
import { getClientUserId } from "@/lib/user";
import { PersonaReactionBubble } from "@/components/PersonaReactionBubble";
import { getMicroQuestTodayCount, getMicroQuestWeeklyCount, recordMicroQuestRun } from "@/lib/microQuestProgress";
import { MicroQuestSummary } from "@/components/micro-quest/MicroQuestSummary";
import { cn } from "@/lib/utils";

type QuestResultEntry = {
  correct: boolean;
  xpAwarded: number;
  personaReaction?: PersonaReaction | null;
  masteryChanges?: MasteryChange[];
};

const DEFAULT_LENGTH = 5;

export default function MicroQuestPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const defaultSkillId = searchParams.get("skill_id");
  const defaultLength = Number(searchParams.get("len")) || DEFAULT_LENGTH;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [questExercises, setQuestExercises] = useState<MicroQuestPlanItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [xpTotal, setXpTotal] = useState(0);
  const [questResults, setQuestResults] = useState<QuestResultEntry[]>([]);
  const [finished, setFinished] = useState(false);
  const [activeExerciseId, setActiveExerciseId] = useState<string | null>(null);
  const [latestReaction, setLatestReaction] = useState<PersonaReaction | null>(null);
  const [latestMastery, setLatestMastery] = useState<MasteryChange[]>([]);
  const [planMeta, setPlanMeta] = useState<MicroQuestPlanResponse | null>(null);
const [todayRuns, setTodayRuns] = useState(() => getMicroQuestTodayCount());
const [weekRuns, setWeekRuns] = useState(() => getMicroQuestWeeklyCount());
const [sessionStart, setSessionStart] = useState<Date | null>(null);

  const prepareQuest = useCallback(
    async (options?: { skillId?: string | null; length?: number }) => {
      setIsLoading(true);
      setError(null);
      setFinished(false);
      setQuestResults([]);
      setLatestReaction(null);
      setLatestMastery([]);
      setXpTotal(0);
      setCurrentIndex(0);
      setActiveExerciseId(null);
      try {
        const length = options?.length ?? defaultLength;
        const skillId = options?.skillId ?? defaultSkillId ?? undefined;
        const plan = await planMicroQuest({ user_id: userId, length, skill_id: skillId });
        setPlanMeta(plan);
        setQuestExercises(plan.items);
        setActiveExerciseId(plan.items[0]?.exercise_id ?? null);
        setSessionStart(new Date());
      } catch (err) {
        console.error(err);
        setError("Could not load a micro-quest right now.");
      } finally {
        setIsLoading(false);
      }
    },
    [defaultLength, defaultSkillId, userId],
  );

  useEffect(() => {
    prepareQuest();
  }, [prepareQuest]);

  const submitSessionLog = useCallback(
    async (results: QuestResultEntry[]) => {
      if (!planMeta || questExercises.length === 0 || results.length === 0) return;
      try {
        const totalQuestions = questExercises.length;
        const correct = results.filter((entry) => entry.correct).length;
        const avgDifficulty =
          questExercises.reduce((sum, item) => sum + item.difficulty, 0) / totalQuestions;
        const reviewFraction =
          questExercises.filter((item) => item.is_review).length / totalQuestions;
        await logPracticeSession({
          user_id: userId,
          skill_id: planMeta.skill_id,
          length: totalQuestions,
          correct_count: correct,
          incorrect_count: totalQuestions - correct,
          avg_difficulty: avgDifficulty,
          fraction_review: reviewFraction,
          started_at: sessionStart?.toISOString(),
          finished_at: new Date().toISOString(),
          abandoned: false,
        });
      } catch (err) {
        console.error("Failed to log practice session", err);
      }
    },
    [planMeta, questExercises, sessionStart, userId],
  );

  const handleComplete = (result: ExerciseResult) => {
    const entry: QuestResultEntry = {
      correct: result.correct,
      xpAwarded: result.xpAwarded ?? 0,
      personaReaction: result.personaReaction,
      masteryChanges: result.masteryChanges,
    };
    const finalResults = [...questResults, entry];
    setQuestResults(finalResults);
    setXpTotal((xp) => xp + (result.xpAwarded ?? 0));
    setLatestReaction(result.personaReaction ?? null);
    setLatestMastery(result.masteryChanges ?? []);

    const nextIndex = currentIndex + 1;
    if (nextIndex >= questExercises.length) {
      setFinished(true);
      setActiveExerciseId(null);
      setSessionStart(null);
      recordMicroQuestRun();
      setTodayRuns(getMicroQuestTodayCount());
      setWeekRuns(getMicroQuestWeeklyCount());
      submitSessionLog(finalResults);
    } else {
      setCurrentIndex(nextIndex);
      setActiveExerciseId(questExercises[nextIndex].exercise_id);
    }
  };

  const masterySummary = useMemo(() => aggregateMastery(questResults), [questResults]);
  const correctCount = questResults.filter((r) => r.correct).length;
  const summaryMessage = buildSummaryMessage(
    questExercises.length > 0 ? correctCount / questExercises.length : 0,
    planMeta?.skill_name,
  );

  const currentExercise = questExercises[currentIndex];
  const progressPercent =
    questExercises.length === 0 ? 0 : (currentIndex / questExercises.length) * 100;

  const renderSkeleton = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-slate-500">Preparing your micro-quest…</p>
      <Skeleton className="mt-4 h-5 w-48" />
      <Skeleton className="mt-2 h-3 w-full" />
      <Skeleton className="mt-2 h-3 w-4/5" />
    </div>
  );

  const renderError = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Could not start a micro-quest</h2>
      <p className="mt-2 text-sm text-slate-500">{error}</p>
      <Button className="mt-4" onClick={() => prepareQuest()}>
        Try again
      </Button>
    </div>
  );

  const renderQuestCard = () => {
    if (questExercises.length === 0) return null;
    return (
      <div className="mx-auto mt-6 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Micro-quest
            </p>
            <h2 className="text-xl font-semibold text-slate-900">
              Question {Math.min(currentIndex + 1, questExercises.length)} of {questExercises.length}
            </h2>
            {planMeta?.skill_name && (
              <p className="text-sm text-slate-500">Focus: {planMeta.skill_name}</p>
            )}
          </div>
          <div className="text-right text-xs text-slate-500">
            <p>XP this run</p>
            <p className="text-lg font-semibold text-slate-900">{xpTotal}</p>
          </div>
        </div>
        <div className="mt-4 h-2 rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-slate-900 transition-all"
            style={{ width: `${Math.min(progressPercent, 100)}%` }}
          />
        </div>
        {currentExercise && (
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
              Difficulty {currentExercise.difficulty}/5
            </span>
            <span
              className={cn(
                "rounded-full px-3 py-1",
                currentExercise.is_review
                  ? "bg-amber-100 text-amber-700"
                  : "bg-emerald-100 text-emerald-700",
              )}
            >
              {currentExercise.is_review ? "Review" : "Challenge"}
            </span>
          </div>
        )}
        {latestReaction && <PersonaReactionBubble reaction={latestReaction} className="mt-4" />}
        {latestMastery.length > 0 && (
          <div className="mt-4 rounded-2xl bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Fresh mastery gains
            </p>
            <div className="mt-2 space-y-1 text-sm text-slate-600">
              {latestMastery.map((change) => (
                <div key={change.skill_id} className="flex items-center justify-between">
                  <span>{change.skill_name}</span>
                  <span>
                    {Math.round(change.old)}% → {Math.round(change.new)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        {!activeExerciseId && !finished && currentExercise && (
          <Button className="mt-4 w-full" onClick={() => setActiveExerciseId(currentExercise.exercise_id)}>
            Resume current exercise
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="mx-auto w-full max-w-4xl pb-16">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Micro-quest</h1>
          <p className="text-sm text-slate-500">Short runs that nudge mastery upward.</p>
        </div>
      </div>

      {isLoading && renderSkeleton()}
      {!isLoading && error && renderError()}
      {!isLoading && !error && !finished && renderQuestCard()}
      {!isLoading && !error && finished && (
        <MicroQuestSummary
          skillName={planMeta?.skill_name}
          totalQuestions={questExercises.length}
          correctCount={correctCount}
          xpTotal={xpTotal}
          masteryDeltas={masterySummary}
          todayRuns={todayRuns}
          weekRuns={weekRuns}
          summaryMessage={summaryMessage}
          onRepeat={() => prepareQuest({ skillId: planMeta?.skill_id, length: questExercises.length || defaultLength })}
          onBack={() => navigate("/today")}
        />
      )}

      <ExerciseModal
        open={Boolean(activeExerciseId)}
        exerciseId={activeExerciseId}
        onClose={() => setActiveExerciseId(null)}
        onComplete={(res) => {
          handleComplete(res);
        }}
      />
    </div>
  );
}

const aggregateMastery = (results: QuestResultEntry[]): MasteryChange[] => {
  const map = new Map<string, MasteryChange>();
  results.forEach((result) => {
    result.masteryChanges?.forEach((change) => {
      const existing = map.get(change.skill_id);
      if (!existing) {
        map.set(change.skill_id, { ...change });
      } else {
        existing.new = change.new;
        existing.delta = change.new - existing.old;
      }
    });
  });
  return Array.from(map.values()).slice(0, 3);
};

const buildSummaryMessage = (ratio: number, skillName?: string | null) => {
  const label = skillName ? `${skillName} reps` : "this run";
  if (ratio >= 0.85) {
    return `You dominated ${label}. Want to try a tougher remix?`;
  }
  if (ratio >= 0.6) {
    return `Nice rhythm on ${label}. A few more runs will lock it in.`;
  }
  return `Good reps even though ${label} pushed back. Small runs build confidence—try another 3-question set.`;
};
