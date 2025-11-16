import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ExerciseModal, type ExerciseResult } from "@/components/ExerciseModal";
import { listExercises, type ExerciseListItem } from "@/api";
import { getClientUserId } from "@/lib/user";

const QUEST_LENGTH = 3;

export default function MicroQuestPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [questExercises, setQuestExercises] = useState<ExerciseListItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [xpTotal, setXpTotal] = useState(0);
  const [firstTryCorrect, setFirstTryCorrect] = useState(0);
  const [finished, setFinished] = useState(false);
  const [activeExerciseId, setActiveExerciseId] = useState<string | null>(null);

  const prepareQuest = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setFinished(false);
    setXpTotal(0);
    setFirstTryCorrect(0);
    setCurrentIndex(0);
    setActiveExerciseId(null);
    try {
      const pool = await listExercises({ user_id: userId });
      let candidates = pool.filter((item) => item.difficulty >= 2 && item.difficulty <= 4);
      if (candidates.length < QUEST_LENGTH) {
        candidates = pool;
      }
      if (candidates.length === 0) {
        throw new Error("No exercises available yet.");
      }
      const shuffled = [...candidates].sort(() => Math.random() - 0.5);
      const selected = shuffled.slice(0, Math.min(QUEST_LENGTH, shuffled.length));
      setQuestExercises(selected);
      setActiveExerciseId(selected[0]?.id ?? null);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Could not load exercises.");
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    prepareQuest();
  }, [prepareQuest]);

  const handleComplete = (result: ExerciseResult) => {
    setXpTotal((xp) => xp + (result.xpAwarded ?? 0));
    if (result.correct) {
      setFirstTryCorrect((count) => count + 1);
    }
    const nextIndex = currentIndex + 1;
    if (nextIndex >= questExercises.length) {
      setFinished(true);
      setActiveExerciseId(null);
    } else {
      setCurrentIndex(nextIndex);
      setActiveExerciseId(questExercises[nextIndex].id);
    }
  };

  const renderSkeleton = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm font-medium text-slate-500">Preparing your micro-quest…</p>
      <Skeleton className="mt-4 h-5 w-40" />
      <Skeleton className="mt-2 h-3 w-full" />
      <Skeleton className="mt-2 h-3 w-5/6" />
    </div>
  );

  const renderError = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Could not start a micro-quest</h2>
      <p className="mt-2 text-sm text-slate-500">{error}</p>
      <Button className="mt-4" onClick={prepareQuest}>
        Try again
      </Button>
    </div>
  );

  const renderSummary = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Quest complete</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">Micro-quest complete</h2>
      <p className="mt-2 text-sm text-slate-600">
        XP gained: <span className="font-semibold">{xpTotal}</span>
      </p>
      <p className="text-sm text-slate-600">
        You nailed {firstTryCorrect} of {questExercises.length} on the first try.
      </p>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row">
        <Button className="w-full" onClick={prepareQuest}>
          Start another micro-quest
        </Button>
        <Button className="w-full" variant="outline" onClick={() => navigate("/exercises")}>
          Back to exercises
        </Button>
      </div>
    </div>
  );

  const renderQuestCard = () => {
    if (questExercises.length === 0) return null;
    const progress = (currentIndex / questExercises.length) * 100;
    return (
      <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Micro-quest</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-900">
          Exercise {Math.min(currentIndex + 1, questExercises.length)} of {questExercises.length}
        </h2>
        <p className="text-sm text-slate-500">Estimated: 8–12 minutes total</p>
        <div className="mt-4 h-2 rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-slate-900 transition-all"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        {!activeExerciseId && !finished && (
          <Button className="mt-4 w-full" onClick={() => setActiveExerciseId(questExercises[currentIndex].id)}>
            Resume current exercise
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="mx-auto w-full max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Micro-quest</h1>
          <p className="text-sm text-slate-500">Complete three targeted exercises to keep your momentum.</p>
        </div>
      </div>

      {isLoading && renderSkeleton()}
      {!isLoading && error && renderError()}
      {!isLoading && !error && finished && renderSummary()}
      {!isLoading && !error && !finished && renderQuestCard()}

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
