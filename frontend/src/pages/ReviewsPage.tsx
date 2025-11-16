import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/sonner";
import {
  getNextReviews,
  postReview,
  type GradeValue,
  type MemoryNext,
} from "@/api";
import { getClientUserId } from "@/lib/user";
import { cn } from "@/lib/utils";

const gradeOptions: { label: string; value: GradeValue; className: string }[] = [
  {
    label: "Again",
    value: 2,
    className: "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
  },
  {
    label: "Hard",
    value: 3,
    className: "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100",
  },
  {
    label: "Good",
    value: 4,
    className: "border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100",
  },
  {
    label: "Easy",
    value: 5,
    className: "border-emerald-300 bg-emerald-100 text-emerald-900 hover:bg-emerald-200",
  },
];

export default function ReviewsPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [queue, setQueue] = useState<MemoryNext[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadReviews = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await getNextReviews(userId, 10);
      setQueue(items);
    } catch (err) {
      console.error(err);
      setError("Could not load your reviews.");
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  const handleGrade = useCallback(
    async (grade: GradeValue) => {
      if (!queue.length || isSubmitting) return;
      const [current, ...rest] = queue;
      setQueue(rest);
      setIsSubmitting(true);
      try {
        const result = await postReview({
          user_id: userId,
          memory_id: current.memory_id,
          grade,
        });
        toast.success(`${result.persona_msg} (+${result.xp_awarded} XP)`);
      } catch (err) {
        console.error(err);
        toast.error("Could not submit review. Please try again.");
        setQueue((prev) => [current, ...prev]);
      } finally {
        setIsSubmitting(false);
      }
    },
    [isSubmitting, queue, userId],
  );

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (isSubmitting || queue.length === 0) return;
      const map: Record<string, GradeValue> = {
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 5,
      };
      const grade = map[event.key];
      if (grade) {
        event.preventDefault();
        handleGrade(grade);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleGrade, isSubmitting, queue.length]);

  const currentCard = queue[0];

  const renderSkeleton = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 p-6 shadow-sm">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="mt-3 h-8 w-3/4" />
      <Skeleton className="mt-2 h-4 w-32" />
      <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Skeleton key={idx} className="h-10 rounded-full" />
        ))}
      </div>
    </div>
  );

  const renderError = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Could not load reviews</h2>
      <p className="mt-2 text-sm text-slate-500">{error}</p>
      <Button className="mt-4" onClick={loadReviews}>
        Retry
      </Button>
    </div>
  );

  const renderEmpty = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 p-6 text-center shadow-sm">
      <p className="text-sm font-medium text-slate-500">Daily review goal met</p>
      <p className="mt-2 text-base text-slate-700">
        You’re up to date. Come back tomorrow or tackle some exercises.
      </p>
      <Button className="mt-4" onClick={() => navigate("/study")}>
        Go to Study
      </Button>
    </div>
  );

  const renderCard = () => {
    if (!currentCard) return null;
    const dueDate = new Date(currentCard.due_at);
    const dueLabel = dueDate.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
    return (
      <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 p-6 shadow-sm">
        <p className="text-sm font-medium text-slate-500">Review</p>
        <p className="mt-2 text-xl font-semibold text-slate-900">{currentCard.concept}</p>
        <p className="mt-1 text-sm text-slate-500">Due: {dueLabel}</p>
        <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
          {gradeOptions.map((option) => (
            <Button
              key={option.value}
              variant="outline"
              disabled={isSubmitting}
              className={cn("rounded-full", option.className)}
              onClick={() => handleGrade(option.value)}
            >
              {option.label}
            </Button>
          ))}
        </div>
        {isSubmitting && (
          <p className="mt-2 text-center text-xs text-slate-500">Submitting...</p>
        )}
      </div>
    );
  };

  if (isLoading) return renderSkeleton();
  if (error) return renderError();
  if (!queue.length) return renderEmpty();
  return renderCard();
}
