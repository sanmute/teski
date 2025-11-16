import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Calendar, CheckCircle2, RefreshCw, Clock3, ClipboardList } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getExamDayPlan,
  getExamOverview,
  postBlockDone,
  postBlockSkip,
  postExamRegenerate,
  type DayBlock,
  type DayPlan,
  type ExamOverview,
} from "@/api";
import { getClientUserId } from "@/lib/user";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/sonner";

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

function formatDayPill(date: Date) {
  return {
    weekday: date.toLocaleDateString(undefined, { weekday: "short" }),
    dayNum: date.getDate(),
  };
}

export default function ExamPage() {
  const { id: examId } = useParams<{ id: string }>();
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();

  const [overview, setOverview] = useState<ExamOverview | null>(null);
  const [dayPlan, setDayPlan] = useState<DayPlan | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [loadingDayPlan, setLoadingDayPlan] = useState(false);
  const [errorOverview, setErrorOverview] = useState<string | null>(null);
  const [errorDayPlan, setErrorDayPlan] = useState<string | null>(null);
  const [regenModalOpen, setRegenModalOpen] = useState(false);
  const [regenIntensity, setRegenIntensity] = useState(3);
  const [regenInFlight, setRegenInFlight] = useState(false);

  const fetchOverview = useCallback(async () => {
    if (!examId) return;
    setLoadingOverview(true);
    setErrorOverview(null);
    try {
      const data = await getExamOverview({ user_id: userId, exam_id: examId });
      setOverview(data);
      const todayIso = new Date().toISOString().slice(0, 10);
      const examDate = data.exam_date;
      const selected = todayIso <= examDate ? todayIso : examDate;
      setSelectedDate(selected);
      setRegenIntensity(data.questionnaire_answer ?? 3);
      await fetchDayPlan(selected, data.id);
    } catch (err) {
      console.error(err);
      setErrorOverview("Could not load exam overview.");
    } finally {
      setLoadingOverview(false);
    }
  }, [examId, userId]);

  const fetchDayPlan = useCallback(
    async (date: string, examIdOverride?: string) => {
      if (!examIdOverride && !examId) return;
      const finalExamId = examIdOverride ?? examId!;
      setLoadingDayPlan(true);
      setErrorDayPlan(null);
      try {
        const plan = await getExamDayPlan({
          user_id: userId,
          exam_id: finalExamId,
          date,
        });
        setDayPlan(plan);
      } catch (err) {
        console.error(err);
        setErrorDayPlan("Could not load this day.");
      } finally {
        setLoadingDayPlan(false);
      }
    },
    [examId, userId],
  );

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  const dayList = useMemo(() => {
    if (!overview) return [];
    const today = new Date();
    const examDate = new Date(overview.exam_date);
    const days: Date[] = [];
    const start = today <= examDate ? today : examDate;
    const current = new Date(start);
    while (current <= examDate) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    if (days.length === 0) days.push(examDate);
    return days;
  }, [overview]);

  const handleBlockAction = async (action: "done" | "skip", block: DayBlock) => {
    if (!examId || !selectedDate) return;
    try {
      if (action === "done") {
        await postBlockDone({ user_id: userId, exam_id: examId, block_id: block.id });
        toast.success("Block marked as done");
      } else {
        await postBlockSkip({ user_id: userId, exam_id: examId, block_id: block.id });
        toast("Block skipped");
      }
      await fetchOverview();
      await fetchDayPlan(selectedDate);
    } catch (err) {
      console.error(err);
      toast.error("Unable to update block. Please try again.");
    }
  };

  const handleRegenerate = async () => {
    if (!examId) return;
    setRegenInFlight(true);
    try {
      await postExamRegenerate({ user_id: userId, exam_id: examId, intensity: regenIntensity });
      toast.success("Plan regenerated");
      setRegenModalOpen(false);
      fetchOverview();
    } catch (err) {
      console.error(err);
      toast.error("Could not regenerate plan.");
    } finally {
      setRegenInFlight(false);
    }
  };

  const renderHeader = () => {
    if (!overview) return null;
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600">
              <ClipboardList className="h-3.5 w-3.5" />
              Exam planner
            </div>
            <h1 className="mt-3 text-2xl font-semibold text-slate-900">{overview.title}</h1>
            {overview.course_name && (
              <p className="text-sm text-slate-500">{overview.course_name}</p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-600">
              <span className="inline-flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(overview.exam_date)}
              </span>
              <span>Days left: {overview.days_left}</span>
            </div>
          </div>
          <Button variant="outline" onClick={() => setRegenModalOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Regenerate plan
          </Button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <div className="rounded-xl bg-slate-100 px-4 py-2 text-sm">
            Total blocks: <span className="font-semibold">{overview.total_blocks}</span>
          </div>
          <div className="rounded-xl bg-slate-100 px-4 py-2 text-sm">
            Remaining: <span className="font-semibold">{overview.remaining_blocks}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderCalendarStrip = () => {
    if (!overview) return null;
    return (
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
        {dayList.map((dateObj) => {
          const iso = dateObj.toISOString().slice(0, 10);
          const { weekday, dayNum } = formatDayPill(dateObj);
          const isSelected = selectedDate === iso;
          return (
            <button
              key={iso}
              className={cn(
                "min-w-[72px] rounded-2xl border px-3 py-2 text-center text-xs font-medium transition",
                isSelected
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
              )}
              onClick={() => {
                setSelectedDate(iso);
                fetchDayPlan(iso);
              }}
            >
              <div>{weekday}</div>
              <div className="text-lg">{dayNum}</div>
            </button>
          );
        })}
      </div>
    );
  };

  const renderBlocks = () => {
    if (loadingDayPlan) {
      return (
        <div className="mt-4 space-y-3">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="mt-2 h-4 w-24" />
              <Skeleton className="mt-3 h-9 w-20 rounded-full" />
            </div>
          ))}
        </div>
      );
    }
    if (errorDayPlan) {
      return (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Could not load this day</h2>
          <p className="mt-2 text-sm text-slate-500">{errorDayPlan}</p>
          <Button className="mt-4" onClick={() => selectedDate && fetchDayPlan(selectedDate)}>
            Retry
          </Button>
        </div>
      );
    }
    if (!dayPlan || dayPlan.blocks.length === 0) {
      return (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-500">No planned blocks for this day</p>
        </div>
      );
    }
    return (
      <div className="mt-4 space-y-3">
        {dayPlan.blocks.map((block) => (
          <div
            key={block.id}
            className={cn(
              "rounded-2xl border border-slate-200 bg-white p-4 shadow-sm",
              block.completed && "bg-slate-50 opacity-70",
            )}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">{block.label}</p>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    {block.type === "mock_exam" ? (
                      <>
                        <ClipboardList className="h-3.5 w-3.5" />
                        Mock exam
                      </>
                    ) : (
                      <>
                        <Clock3 className="h-3.5 w-3.5" />
                        Study block
                      </>
                    )}
                  </span>
                  <span>{block.duration_minutes} min</span>
                </div>
              </div>
              {block.completed ? (
                <div className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                  Completed
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => handleBlockAction("done", block)}>
                    Done
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleBlockAction("skip", block)}>
                    Skip
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loadingOverview) {
    return (
      <div className="mx-auto w-full max-w-4xl space-y-4">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-16 w-full rounded-2xl" />
        <Skeleton className="h-48 w-full rounded-2xl" />
      </div>
    );
  }

  if (errorOverview || !examId) {
    return (
      <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Could not load exam plan</h2>
        <p className="mt-2 text-sm text-slate-500">{errorOverview ?? "Invalid exam identifier."}</p>
        <Button className="mt-4" onClick={fetchOverview}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl">
      {renderHeader()}
      {renderCalendarStrip()}
      {renderBlocks()}

      {regenModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          role="dialog"
          aria-modal="true"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setRegenModalOpen(false);
            }
          }}
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Regenerate plan</h2>
              <button
                className="rounded-full p-1 text-slate-400 hover:text-slate-600"
                aria-label="Close"
                onClick={() => setRegenModalOpen(false)}
              >
                ×
              </button>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              Regenerating will reshuffle remaining blocks while keeping completed work intact.
            </p>
            <div className="mt-4">
              <p className="text-sm font-medium text-slate-700">How intense should the plan be?</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={cn(
                      "rounded-full border px-3 py-1 text-sm",
                      regenIntensity === value
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                    )}
                    onClick={() => setRegenIntensity(value)}
                  >
                    {value} {value === 1 ? "Very light" : value === 5 ? "Very intense" : ""}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setRegenModalOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleRegenerate} disabled={regenInFlight}>
                {regenInFlight ? "Regenerating..." : "Regenerate"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
