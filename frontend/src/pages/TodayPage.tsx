import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ClipboardList, Clock3, BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getPersona,
  getTodayAgenda,
  postBlockDone,
  postBlockSkip,
  type PersonaOut,
  type TodayAgendaOut,
  type TodayItem,
} from "@/api";
import { getClientUserId } from "@/lib/user";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/sonner";
import { DailyPracticeCard } from "@/components/DailyPracticeCard";

export default function TodayPage() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [agenda, setAgenda] = useState<TodayAgendaOut | null>(null);
  const [persona, setPersona] = useState<PersonaOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBlock, setSelectedBlock] = useState<Extract<TodayItem, { kind: "study_block" }> | null>(null);
  const [isBlockModalOpen, setIsBlockModalOpen] = useState(false);

  const [examId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem("teski-active-exam-id");
  });

  const fetchAgenda = useCallback(async () => {
    if (!examId) {
      setIsLoading(false);
      setAgenda(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await getTodayAgenda({ user_id: userId, exam_id: examId });
      setAgenda(data);
    } catch (err) {
      console.error(err);
      setError("Could not load today's agenda.");
    } finally {
      setIsLoading(false);
    }
  }, [examId, userId]);

  useEffect(() => {
    fetchAgenda();
  }, [fetchAgenda]);

  useEffect(() => {
    getPersona(userId)
      .then(setPersona)
      .catch((err) => console.error(err));
  }, [userId]);

  const handleStart = (item: TodayItem) => {
    if (item.kind === "review_due") {
      navigate("/reviews");
      return;
    }
    setSelectedBlock(item);
    setIsBlockModalOpen(true);
  };

  const handleBlockAction = async (
    action: "done" | "skip",
    block: Extract<TodayItem, { kind: "study_block" }>,
  ) => {
    if (!examId) return;
    try {
      if (action === "done") {
        await postBlockDone({ user_id: userId, exam_id: examId, block_id: block.block_id });
        toast.success("Block marked as done");
      } else {
        await postBlockSkip({ user_id: userId, exam_id: examId, block_id: block.block_id });
        toast("Block skipped for now");
      }
      setIsBlockModalOpen(false);
      setSelectedBlock(null);
      fetchAgenda();
    } catch (err) {
      console.error(err);
      toast.error("Unable to update this block. Please try again.");
    }
  };

  const personaLine = agenda?.persona_line || persona?.warmup_line || persona?.short_line;

  const renderSkeletons = () => (
    <div className="mt-4 space-y-3">
      {Array.from({ length: 3 }).map((_, idx) => (
        <div key={idx} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="mt-2 h-4 w-24" />
        </div>
      ))}
    </div>
  );

  const renderError = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Could not load today&apos;s agenda</h2>
      <p className="mt-2 text-sm text-slate-500">{error}</p>
      <Button className="mt-4" onClick={fetchAgenda}>
        Retry
      </Button>
    </div>
  );

  const renderEmpty = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <p className="text-sm font-medium text-slate-500">Nothing scheduled for today</p>
      <p className="mt-2 text-base text-slate-700">You can still review or practice exercises.</p>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
        <Button onClick={() => navigate("/reviews")}>Go to Reviews</Button>
        <Button variant="outline" onClick={() => navigate("/exercises")}>
          Browse Exercises
        </Button>
      </div>
    </div>
  );

  const renderNoExam = () => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <p className="text-sm font-medium text-slate-500">No exam plan linked</p>
      <p className="mt-2 text-base text-slate-700">Once you start an exam plan, your daily agenda will appear here.</p>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
        <Button onClick={() => navigate("/reviews")}>Start reviews</Button>
        <Button variant="outline" onClick={() => navigate("/exercises")}>
          Browse exercises
        </Button>
      </div>
    </div>
  );

  const renderItems = () => (
    <div className="mt-4 space-y-3">
      {agenda?.items.map((item) => (
        <div
          key={item.id}
          className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-slate-100 p-2 text-slate-600">
              {item.kind === "review_due" ? <BookOpen className="h-4 w-4" /> : <Clock3 className="h-4 w-4" />}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">{item.label}</p>
              {item.kind === "study_block" && (
                <p className="text-xs text-slate-500">
                  {item.course_name ?? "Study block"} · {item.duration_minutes} min
                </p>
              )}
            </div>
          </div>
          <Button className="self-start" onClick={() => handleStart(item)}>
            Start
          </Button>
        </div>
      ))}
    </div>
  );

  return (
    <div className="mx-auto w-full max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Today</h1>
        {personaLine && <p className="mt-1 text-sm text-slate-500">Teski says: {personaLine}</p>}
        <button
          type="button"
          onClick={() => navigate("/skills")}
          className="mt-2 text-sm font-semibold text-slate-700 underline-offset-2 hover:underline"
        >
          View your skill map
        </button>
      </div>
      <DailyPracticeCard userId={userId} />
      {isLoading && renderSkeletons()}
      {!isLoading && error && renderError()}
      {!isLoading && !error && !examId && renderNoExam()}
      {!isLoading && !error && examId && agenda && agenda.items.length === 0 && renderEmpty()}
      {!isLoading && !error && examId && agenda && agenda.items.length > 0 && renderItems()}
      {isBlockModalOpen && selectedBlock && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          role="dialog"
          aria-modal="true"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setIsBlockModalOpen(false);
              setSelectedBlock(null);
            }
          }}
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{selectedBlock.label}</h2>
                <p className="text-xs text-slate-500">
                  {selectedBlock.course_name ?? "Study block"} · {selectedBlock.duration_minutes} min
                </p>
              </div>
              <button
                className="rounded-full p-1 text-slate-400 hover:text-slate-600"
                aria-label="Close"
                onClick={() => {
                  setIsBlockModalOpen(false);
                  setSelectedBlock(null);
                }}
              >
                ×
              </button>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Focus on this block, then mark it as done or skip it if you want to revisit later.
            </p>
            <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <Button variant="ghost" onClick={() => navigate("/exercises")}>
                Open related exercises
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => handleBlockAction("skip", selectedBlock)}>
                  Skip
                </Button>
                <Button onClick={() => handleBlockAction("done", selectedBlock)}>Done</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
