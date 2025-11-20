import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getExercise,
  submitExercise,
  type ExerciseGetOut,
  type ExerciseSubmitOut,
  type PersonaReaction,
  type MasteryChange,
} from "@/api";
import { getClientUserId } from "@/lib/user";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/sonner";
import { PersonaReactionBubble } from "@/components/PersonaReactionBubble";

export type ExerciseResult = {
  exerciseId: string;
  correct: boolean;
  xpAwarded: number;
  personaReaction?: PersonaReaction | null;
  masteryChanges?: MasteryChange[];
};

interface ExerciseModalProps {
  open: boolean;
  exerciseId: string | null;
  onClose: () => void;
  onOpenExercise?: (exerciseId: string) => void;
  onComplete?: (result: ExerciseResult) => void;
}

export function ExerciseModal({
  open,
  exerciseId,
  onClose,
  onOpenExercise,
  onComplete,
}: ExerciseModalProps) {
  const userId = useMemo(() => getClientUserId(), []);
  const [loading, setLoading] = useState(false);
  const [exercise, setExercise] = useState<ExerciseGetOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [hintShown, setHintShown] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ExerciseSubmitOut | null>(null);
  const [personaReaction, setPersonaReaction] = useState<PersonaReaction | null>(null);

  const closeAndReset = useCallback(() => {
    setExercise(null);
    setAnswer("");
    setHintShown(false);
    setSubmitting(false);
    setResult(null);
    setError(null);
    setPersonaReaction(null);
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open || !exerciseId) return;
    setLoading(true);
    setExercise(null);
    setAnswer("");
    setHintShown(false);
    setResult(null);
    setError(null);
    setPersonaReaction(null);
    getExercise(userId, exerciseId)
      .then((data) => setExercise(data))
      .catch((err) => {
        console.error(err);
        setError("Could not load this exercise.");
      })
      .finally(() => setLoading(false));
  }, [exerciseId, open, userId]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeAndReset();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [closeAndReset, open]);

  useEffect(() => {
    if (result?.correct) {
      const timer = setTimeout(() => {
        closeAndReset();
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [closeAndReset, result]);

  useEffect(() => {
    if (!personaReaction) return;
    const timer = setTimeout(() => setPersonaReaction(null), 4000);
    return () => clearTimeout(timer);
  }, [personaReaction]);

  const buildAnswerPayload = () => {
    if (!exercise) {
      throw new Error("No exercise loaded");
    }
    if (exercise.type === "MCQ") {
      const index = Number(answer);
      if (Number.isNaN(index)) {
        throw new Error("Select an option");
      }
      return { choice: index };
    }
    if (exercise.type === "NUMERIC") {
      const trimmed = answer.trim();
      const value = Number(trimmed);
      if (Number.isNaN(value)) {
        throw new Error("Enter a number");
      }
      return { value };
    }
    const text = answer.trim();
    if (!text) {
      throw new Error("Enter your answer");
    }
    return { text };
  };

  const handleSubmit = async () => {
    if (!exercise) return;
    setSubmitting(true);
    try {
      const answerPayload = buildAnswerPayload();
      const data = await submitExercise({
        user_id: userId,
        exercise_id: exercise.id,
        answer: answerPayload,
      });
      setResult(data);
      setPersonaReaction(data.persona_reaction ?? null);
      if (data.correct) {
        toast.success(`${data.persona_msg ?? "Nice work!"} (+${data.xp_awarded} XP)`);
      } else {
        toast(data.persona_msg ?? "Logged for review.");
      }
      if (exercise) {
        onComplete?.({
          exerciseId: exercise.id,
          correct: data.correct,
          xpAwarded: data.xp_awarded ?? 0,
          personaReaction: data.persona_reaction ?? null,
          masteryChanges: data.mastery_changes ?? [],
        });
      }
    } catch (err) {
      console.error(err);
      toast.error("Could not submit answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="mt-3 h-4 w-52" />
          <Skeleton className="mt-4 h-20 w-full" />
        </div>
      );
    }
    if (error) {
      return (
        <div className="text-center">
          <p className="text-sm text-slate-500">{error}</p>
          <Button className="mt-4" onClick={closeAndReset}>
            Close
          </Button>
        </div>
      );
    }
    if (!exercise) return null;

    const typeLabel =
      exercise.type === "MCQ"
        ? "Multiple choice"
        : exercise.type === "NUMERIC"
          ? "Numeric answer"
          : "Short answer";

    return (
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="exercise-modal-title" className="text-lg font-semibold text-slate-900">
              {exercise.concept}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-600">
              <span className="rounded-full border border-slate-200 px-2 py-0.5">{typeLabel}</span>
              <span>Difficulty: {exercise.difficulty} / 5</span>
            </div>
          </div>
          <button
            type="button"
            onClick={closeAndReset}
            className="rounded-full border border-transparent p-1 text-slate-400 hover:text-slate-600"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <p className="mt-4 text-sm text-slate-700 whitespace-pre-line">{exercise.prompt}</p>

        {exercise.hint && !hintShown && (
          <button
            type="button"
            onClick={() => setHintShown(true)}
            className="mt-3 text-sm font-medium text-slate-600 underline-offset-2 hover:underline"
          >
            Show hint
          </button>
        )}
        {exercise.hint && hintShown && (
          <div className="mt-3 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
            {exercise.hint.split(". ")[0] + "."}
            <p className="mt-2 text-xs text-slate-500">Using hints may reduce XP for this question.</p>
          </div>
        )}

        <div className="mt-4">{renderAnswerField(exercise)}</div>

        {result && (
          <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700">
            {result.correct ? "Marked correct." : "Logged for review."}
            {result.detector_subtype && (
              <span className="ml-2 inline-flex items-center rounded-full bg-white px-2 py-0.5 text-xs text-slate-600">
                {detectorLabel(result.detector_subtype)}
              </span>
            )}
            {result.explanation && (
              <p className="mt-2 text-sm text-slate-600">{result.explanation}</p>
            )}
            {!result.correct && result.related_exercise_id && onOpenExercise && (
              <Button
                variant="outline"
                className="mt-3"
                onClick={() => {
                  closeAndReset();
                  onOpenExercise(result.related_exercise_id);
                }}
              >
                Try a related exercise
              </Button>
            )}
          </div>
        )}

        <PersonaReactionBubble reaction={personaReaction} />

        <div className="mt-6 flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={closeAndReset}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!answer.trim() || submitting}>
            {result?.correct ? "Great job!" : submitting ? "Submitting..." : "Submit"}
          </Button>
        </div>
      </div>
    );
  };

  const renderAnswerField = (exercise: ExerciseGetOut) => {
    if (exercise.type === "MCQ" && exercise.choices) {
      return (
        <div className="space-y-2">
          {exercise.choices.map((choice, idx) => {
            const choiceText = typeof choice === "string" ? choice : choice?.text ?? "";
            return (
              <label
                key={idx}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2",
                  answer === String(idx) ? "border-slate-900 bg-slate-900/5" : "border-slate-200",
                )}
              >
                <input
                  type="radio"
                  name="exercise-choice"
                  value={idx}
                  checked={answer === String(idx)}
                  onChange={() => setAnswer(String(idx))}
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
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Enter numeric answer"
          />
          {exercise.unit_hint && (
            <p className="mt-1 text-xs text-slate-500">Unit: {exercise.unit_hint}</p>
          )}
        </div>
      );
    }

    return (
      <div>
        <Textarea
          value={answer}
          onChange={(e) => {
            const val = e.target.value.slice(0, 300);
            setAnswer(val);
          }}
          rows={4}
          placeholder="Type your answer..."
        />
        <p className="mt-1 text-xs text-slate-500">{answer.length} / 300</p>
      </div>
    );
  };

  const detectorLabel = (subtype: NonNullable<ExerciseSubmitOut["detector_subtype"]>) => {
    switch (subtype) {
      case "unit":
        return "Unit issue";
      case "sign":
        return "Sign issue";
      case "rounding":
        return "Rounding issue";
      case "near_miss":
        return "Near miss";
      default:
        return "Hint";
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="exercise-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          closeAndReset();
        }
      }}
    >
      <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl">{renderContent()}</div>
    </div>
  );
}
