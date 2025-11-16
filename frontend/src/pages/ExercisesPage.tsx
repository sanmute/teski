import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ExerciseModal } from "@/components/ExerciseModal";
import { listExercises, type ExerciseListItem } from "@/api";
import { getClientUserId } from "@/lib/user";
import { cn } from "@/lib/utils";

type ExerciseTypeFilter = "ALL" | "MCQ" | "NUMERIC" | "SHORT";

const typeChips: { label: string; value: ExerciseTypeFilter }[] = [
  { label: "All", value: "ALL" },
  { label: "MCQ", value: "MCQ" },
  { label: "Numeric", value: "NUMERIC" },
  { label: "Short answer", value: "SHORT" },
];

export default function ExercisesPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [items, setItems] = useState<ExerciseListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedType, setSelectedType] = useState<ExerciseTypeFilter>("ALL");
  const [difficultyRange, setDifficultyRange] = useState<[number, number]>([1, 5]);
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | null>(null);
  const [isExerciseOpen, setIsExerciseOpen] = useState(false);

  const fetchExercises = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listExercises({
        user_id: userId,
        search,
        type: selectedType === "ALL" ? undefined : selectedType,
        difficultyMin: difficultyRange[0],
        difficultyMax: difficultyRange[1],
      });
      setItems(data);
    } catch (err) {
      console.error(err);
      setError("Could not load exercises.");
    } finally {
      setIsLoading(false);
    }
  }, [difficultyRange, search, selectedType, userId]);

  useEffect(() => {
    fetchExercises();
  }, [fetchExercises]);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch = item.concept.toLowerCase().includes(search.toLowerCase());
      const matchesType = selectedType === "ALL" || item.type === selectedType;
      const matchesDifficulty =
        item.difficulty >= difficultyRange[0] && item.difficulty <= difficultyRange[1];
      return matchesSearch && matchesType && matchesDifficulty;
    });
  }, [difficultyRange, items, search, selectedType]);

  const handleDifficultyChange = (index: 0 | 1, value: number) => {
    const clamped = Math.min(5, Math.max(1, value));
    setDifficultyRange((prev) => {
      const next: [number, number] = [...prev] as [number, number];
      next[index] = clamped;
      if (next[0] > next[1]) {
        if (index === 0) next[1] = clamped;
        else next[0] = clamped;
      }
      return next;
    });
  };

const renderSkeletons = () => (
    <div className="mx-auto mt-4 w-full max-w-3xl space-y-3">
      {Array.from({ length: 4 }).map((_, idx) => (
        <div
          key={idx}
          className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm animate-pulse"
        >
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-24" />
          </div>
          <Skeleton className="mt-4 h-9 w-24 rounded-full" />
        </div>
      ))}
    </div>
  );

  const renderError = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Could not load exercises</h2>
      <p className="mt-2 text-sm text-slate-500">{error}</p>
      <Button className="mt-4" onClick={fetchExercises}>
        Retry
      </Button>
    </div>
  );

  const renderEmpty = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <p className="text-sm font-medium text-slate-500">No exercises found</p>
      <p className="mt-2 text-base text-slate-700">
        Try adjusting your filters or catch up on reviews.
      </p>
      <Button className="mt-4" onClick={() => navigate("/reviews")}>
        Go to Reviews
      </Button>
    </div>
  );

  const renderFilters = () => (
    <div className="mx-auto mt-4 w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <div>
        <label className="text-xs font-medium text-slate-500">Search</label>
        <Input
          type="search"
          placeholder="Search concepts…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-1"
        />
      </div>
      <div className="mt-4">
        <p className="text-xs font-medium text-slate-500">Type</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {typeChips.map((chip) => (
            <button
              key={chip.value}
              type="button"
              onClick={() => setSelectedType(chip.value)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition",
                selectedType === chip.value
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
              )}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4">
        <p className="text-xs font-medium text-slate-500 mb-2">Difficulty</p>
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Input
            type="number"
            min={1}
            max={5}
            value={difficultyRange[0]}
            onChange={(e) => handleDifficultyChange(0, Number(e.target.value))}
            className="w-16"
          />
          <span>–</span>
          <Input
            type="number"
            min={1}
            max={5}
            value={difficultyRange[1]}
            onChange={(e) => handleDifficultyChange(1, Number(e.target.value))}
            className="w-16"
          />
        </div>
      </div>
    </div>
  );

  const renderList = () => (
    <div className="mx-auto mt-4 w-full max-w-3xl space-y-3">
      {filteredItems.map((item) => (
        <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-base font-semibold text-slate-900">{item.concept}</p>
              <p className="text-xs text-slate-500">Difficulty: {item.difficulty} / 5</p>
            </div>
            <span className="rounded-full border border-slate-200 px-3 py-0.5 text-xs font-medium text-slate-600">
              {item.type}
            </span>
          </div>
          {item.tags && item.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {item.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          <div className="mt-4 flex justify-end">
            <Button
              onClick={() => {
                setSelectedExerciseId(item.id);
                setIsExerciseOpen(true);
              }}
            >
              Open
            </Button>
          </div>
        </div>
      ))}
    </div>
  );

  if (isLoading && items.length === 0) {
    return (
      <>
        {renderFilters()}
        {renderSkeletons()}
      </>
    );
  }

  if (error) {
    return (
      <>
        {renderFilters()}
        {renderError()}
      </>
    );
  }

  const renderMicroQuestCard = () => (
    <div className="mx-auto mt-4 w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Micro-quest</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">Let Teski pick 3 exercises for you</h2>
      <p className="mt-1 text-sm text-slate-600">
        A quick trio tailored to your current level. Earn bonus XP and keep your streak alive.
      </p>
      <Button className="mt-4" onClick={() => navigate("/micro-quest")}>
        Start micro-quest
      </Button>
    </div>
  );

  return (
    <>
      {renderMicroQuestCard()}
      {renderFilters()}
      {filteredItems.length === 0 ? renderEmpty() : renderList()}
      <ExerciseModal
        open={isExerciseOpen}
        exerciseId={selectedExerciseId}
        onClose={() => {
          setIsExerciseOpen(false);
          setSelectedExerciseId(null);
        }}
        onOpenExercise={(id) => {
          setSelectedExerciseId(id);
          setIsExerciseOpen(true);
        }}
      />
    </>
  );
}
