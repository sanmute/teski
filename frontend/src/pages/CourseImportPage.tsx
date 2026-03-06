import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  CheckCircle2,
  Circle,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  BookOpen,
  Loader2,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/sonner";
import {
  searchCourses,
  generateFromExams,
  saveExercises,
} from "@/api/examPipeline";
import type { ExamResult, GeneratedExerciseOut, PipelineResponse } from "@/api/examPipeline";

// ── Constants ────────────────────────────────────────────────────────────────

type Step = 1 | 2 | 3 | 4;

const STEP_LABELS: string[] = ["Search", "Select", "Generate", "Review"];

const TYPE_COLORS: Record<string, string> = {
  mcq: "bg-blue-100 text-blue-700",
  numeric: "bg-emerald-100 text-emerald-700",
  short_answer: "bg-violet-100 text-violet-700",
};

const TYPE_LABELS: Record<string, string> = {
  mcq: "MCQ",
  numeric: "Numeric",
  short_answer: "Short answer",
};

// ── Sub-components ───────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: Step }) {
  return (
    <div className="flex items-center gap-2">
      {STEP_LABELS.map((label, i) => {
        const n = (i + 1) as Step;
        const isActive = current === n;
        const isDone = current > n;
        return (
          <div key={label} className="flex items-center gap-2">
            <div
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition",
                isActive && "bg-slate-900 text-white",
                isDone && "bg-slate-200 text-slate-500",
                !isActive && !isDone && "border border-slate-200 text-slate-400",
              )}
            >
              {isDone ? "✓" : n}
            </div>
            <span
              className={cn(
                "hidden text-xs font-medium sm:block",
                isActive ? "text-slate-900" : "text-slate-400",
              )}
            >
              {label}
            </span>
            {i < STEP_LABELS.length - 1 && (
              <div className="h-px w-4 bg-slate-200" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function DifficultyDots({ value }: { value: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={cn(
            "inline-block h-2 w-2 rounded-full",
            i < value ? "bg-slate-700" : "bg-slate-200",
          )}
        />
      ))}
    </span>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function CourseImportPage() {
  const navigate = useNavigate();

  // Step routing
  const [step, setStep] = useState<Step>(1);

  // Step 1
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  // Step 2
  const [searchResults, setSearchResults] = useState<ExamResult[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());

  // Step 3
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [progressPct, setProgressPct] = useState(8);
  const generateCalledRef = useRef(false);

  // Step 4
  const [pipelineResponse, setPipelineResponse] = useState<PipelineResponse | null>(null);
  const [reviewMode, setReviewMode] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);

  // ── Step 3 auto-trigger ────────────────────────────────────────────────────
  useEffect(() => {
    if (step !== 3) return;
    if (generateCalledRef.current) return;
    generateCalledRef.current = true;

    // Kick off slow progress bar animation
    const progressTimer = setTimeout(() => setProgressPct(85), 300);

    const validUrls = Array.from(selectedUrls).filter(
      (url) => url && url.endsWith(".pdf"),
    );
    const selectedExam = searchResults.find((r) => validUrls.includes(r.pdf_url));
    const courseName = selectedExam?.course_name ?? query;

    (async () => {
      try {
        if (validUrls.length === 0) {
          throw new Error(
            "None of the selected courses have exam PDFs available.",
          );
        }
        const res = await generateFromExams({
          course_name: courseName,
          pdf_urls: validUrls,
          num_exercises: 10,
        });
        setPipelineResponse(res);
        setStep(4);
      } catch (err) {
        setGenerateError(
          err instanceof Error ? err.message : "Generation failed. Please try again.",
        );
      } finally {
        clearTimeout(progressTimer);
      }
    })();
  }, [step]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const res = await searchCourses(query.trim());
      if (res.results.length === 0) {
        toast("No exams found", {
          description: `No archived exams matched "${query}". Try a shorter query or course code.`,
        });
        return;
      }
      setSearchResults(res.results);
      setSelectedUrls(new Set());
      setStep(2);
    } catch (err) {
      toast("Search failed", {
        description:
          err instanceof Error ? err.message : "Could not reach the exam archive.",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSelect = (url: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(url)) {
        next.delete(url);
      } else if (next.size < 3) {
        next.add(url);
      } else {
        toast("Maximum 3 exams", {
          description: "Deselect one before adding another.",
        });
      }
      return next;
    });
  };

  const goToGenerate = () => {
    generateCalledRef.current = false;
    setGenerateError(null);
    setPipelineResponse(null);
    setProgressPct(8);
    setStep(3);
  };

  const handleSave = async () => {
    if (!pipelineResponse) return;
    setIsSaving(true);
    try {
      const res = await saveExercises(pipelineResponse.exercises);
      const n = res.saved.length;
      toast("Exercises saved!", {
        description: `${n} new exercise${n !== 1 ? "s" : ""} added to your practice set.`,
      });
      navigate("/exercises");
    } catch (err) {
      toast("Save failed", {
        description:
          err instanceof Error ? err.message : "Could not save exercises.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-8 px-4 py-10 sm:px-6">
      <StepIndicator current={step} />

      {/* ── Step 1: Search ── */}
      {step === 1 && (
        <div className="flex flex-col gap-6">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Import from past exams
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
              What course are you studying?
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              We'll search the LUT exam archive and build practice exercises from real past papers.
            </p>
          </div>

          <div className="flex gap-3">
            <Input
              autoFocus
              placeholder="e.g. Statistics I or BM20A8601"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="text-base"
            />
            <Button onClick={handleSearch} disabled={isSearching || !query.trim()}>
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="ml-2">{isSearching ? "Searching…" : "Search"}</span>
            </Button>
          </div>
        </div>
      )}

      {/* ── Step 2: Select exams ── */}
      {step === 2 && (
        <div className="flex flex-col gap-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                Select exam papers
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Choose up to 3 past papers. More papers means more variety.
              </p>
            </div>
            {selectedUrls.size > 0 && (
              <span className="mt-1 inline-flex h-7 w-10 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                {selectedUrls.size}/3
              </span>
            )}
          </div>

          <div className="space-y-3">
            {searchResults.map((exam) => {
              const hasExams = exam.has_exams && !!exam.pdf_url && exam.pdf_url.endsWith(".pdf");
              const isSelected = hasExams && selectedUrls.has(exam.pdf_url);

              if (!hasExams) {
                return (
                  <div
                    key={exam.course_code}
                    className="w-full rounded-2xl border border-slate-100 bg-slate-50 p-4 text-left opacity-60"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-semibold text-slate-500">
                          {exam.course_name}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-400">
                          {exam.course_code && (
                            <span className="mr-2 font-mono">{exam.course_code}</span>
                          )}
                          {exam.department}
                        </p>
                        <p className="mt-1 text-xs text-slate-400 italic">
                          No past exams uploaded yet
                        </p>
                      </div>
                      <Circle className="mt-0.5 h-5 w-5 flex-shrink-0 text-slate-200" />
                    </div>
                  </div>
                );
              }

              return (
                <button
                  key={exam.course_code}
                  type="button"
                  onClick={() => toggleSelect(exam.pdf_url)}
                  className={cn(
                    "w-full rounded-2xl border p-4 text-left transition-all",
                    isSelected
                      ? "border-slate-900 bg-slate-50 shadow-sm"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-slate-900">
                        {exam.course_name}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {exam.course_code && (
                          <span className="mr-2 font-mono">{exam.course_code}</span>
                        )}
                        {exam.department}
                        {exam.date && (
                          <span className="ml-2 text-slate-400">{exam.date}</span>
                        )}
                      </p>
                    </div>
                    {isSelected ? (
                      <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-slate-900" />
                    ) : (
                      <Circle className="mt-0.5 h-5 w-5 flex-shrink-0 text-slate-300" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          <p className="text-xs text-slate-400">
            Source: LUT exam archive (exams.ltky.fi) — open student archive. Ensure
            your use complies with your institution's policy.
          </p>

          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button disabled={selectedUrls.size === 0} onClick={goToGenerate}>
              Generate practice exercises
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ── Step 3: Generating ── */}
      {step === 3 && (
        <div className="flex flex-col gap-6">
          {generateError ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="font-semibold">Generation failed</p>
              </div>
              <p className="mt-1 text-sm text-red-600">{generateError}</p>
              <div className="mt-4 flex gap-3">
                <Button variant="secondary" onClick={() => setStep(2)}>
                  Back to selection
                </Button>
                <Button onClick={goToGenerate}>Try again</Button>
              </div>
            </div>
          ) : (
            <>
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                  Generating your practice set…
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  Reading {selectedUrls.size} exam paper
                  {selectedUrls.size !== 1 ? "s" : ""} and creating exercises.
                  This usually takes 15–30 seconds.
                </p>
              </div>

              {/* Smooth progress bar */}
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-800 transition-[width] duration-[25000ms] ease-out"
                  style={{ width: `${progressPct}%` }}
                />
              </div>

              {/* Exercise placeholder skeletons */}
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                      <Skeleton className="h-6 w-16 rounded-full" />
                    </div>
                    <div className="mt-3 flex items-center gap-1.5">
                      {Array.from({ length: 5 }).map((_, j) => (
                        <Skeleton key={j} className="h-2 w-2 rounded-full" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Step 4: Review and save ── */}
      {step === 4 && pipelineResponse && (
        <div className="flex flex-col gap-5">
          {/* Success banner */}
          <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600" />
            <div>
              <p className="font-semibold text-emerald-900">
                {pipelineResponse.exercises.length} exercises generated for{" "}
                <span className="italic">{pipelineResponse.course_name}</span>
              </p>
              <p className="mt-0.5 text-sm text-emerald-700">
                Based on {pipelineResponse.pdf_count} exam paper
                {pipelineResponse.pdf_count !== 1 ? "s" : ""}. Ready to add to
                your practice set.
              </p>
            </div>
          </div>

          {/* Exercise list */}
          <div className="space-y-3">
            {pipelineResponse.exercises.map((ex: GeneratedExerciseOut) => {
              const isExpanded = expandedIds.has(ex.id);
              return (
                <div
                  key={ex.id}
                  className="rounded-2xl border border-slate-200 bg-white shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3 p-4">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-slate-900">
                        {ex.concept}
                      </p>
                      <div className="mt-1.5 flex items-center gap-2">
                        <DifficultyDots value={ex.difficulty} />
                        <span className="text-xs text-slate-400">
                          {ex.difficulty}/5
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-shrink-0 items-center gap-2">
                      <span
                        className={cn(
                          "rounded-full px-2.5 py-0.5 text-xs font-medium",
                          TYPE_COLORS[ex.type] ?? "bg-slate-100 text-slate-600",
                        )}
                      >
                        {TYPE_LABELS[ex.type] ?? ex.type}
                      </span>
                      {reviewMode && (
                        <button
                          type="button"
                          onClick={() => toggleExpanded(ex.id)}
                          className="text-slate-400 hover:text-slate-700"
                          aria-label={isExpanded ? "Collapse" : "Expand"}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {reviewMode && isExpanded && (
                    <div className="space-y-3 border-t border-slate-100 px-4 pb-4 pt-3">
                      <p className="text-sm text-slate-700">{ex.question}</p>
                      {ex.explanation && (
                        <div className="rounded-lg bg-slate-50 p-3">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                            Explanation
                          </p>
                          <p className="mt-1 text-sm text-slate-600">
                            {ex.explanation}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Action buttons */}
          {!reviewMode ? (
            <div className="flex flex-wrap gap-3">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <BookOpen className="mr-2 h-4 w-4" />
                )}
                {isSaving ? "Saving…" : "Start practising"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setReviewMode(true);
                  setExpandedIds(new Set());
                }}
              >
                Review first
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-4">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <BookOpen className="mr-2 h-4 w-4" />
                )}
                {isSaving ? "Saving…" : "Save and practise"}
              </Button>
              <Button variant="secondary" onClick={() => setReviewMode(false)}>
                Back to summary
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
