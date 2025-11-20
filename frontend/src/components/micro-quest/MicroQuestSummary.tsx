import { Fragment } from "react";
import { Sparkles, Repeat, Home } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MasteryBar } from "@/components/MasteryBar";
import { DAILY_MICROQUEST_GOAL, WEEKLY_MICROQUEST_GOAL } from "@/lib/practiceGoals";

type MasteryDelta = {
  skill_id: string;
  skill_name: string;
  old: number;
  new: number;
};

type MicroQuestSummaryProps = {
  skillId?: string;
  skillName?: string;
  totalQuestions: number;
  correctCount: number;
  xpTotal: number;
  masteryDeltas: MasteryDelta[];
  todayRuns: number;
  weekRuns: number;
  summaryMessage: string;
  runReaction?: string;
  streakAfter?: number | null;
  ctaLabel?: string;
  onRepeat: () => void;
  onBack: () => void;
  onOpenSkillMap?: () => void;
};

export function MicroQuestSummary({
  skillId,
  skillName,
  totalQuestions,
  correctCount,
  xpTotal,
  masteryDeltas,
  todayRuns,
  weekRuns,
  summaryMessage,
  runReaction,
  streakAfter,
  ctaLabel,
  onRepeat,
  onBack,
  onOpenSkillMap,
}: MicroQuestSummaryProps) {
  const accuracy = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;

  return (
    <div className="mx-auto mt-6 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-full bg-slate-900/10 p-3 text-slate-900">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Micro-quest complete
          </p>
          <h2 className="text-2xl font-semibold text-slate-900">
            {skillName ? `Progress in ${skillName}` : "Session finished"}
          </h2>
      </div>
    </div>
      <p className="mt-3 text-sm text-slate-600">{summaryMessage}</p>
      {runReaction && <p className="mt-2 text-sm font-medium text-slate-800">{runReaction}</p>}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <SummaryStat label="Accuracy" value={`${accuracy}%`} />
        <SummaryStat label="XP earned" value={`+${xpTotal}`} />
        <SummaryStat label="Correct" value={`${correctCount}/${totalQuestions}`} />
      </div>

      {typeof streakAfter === "number" && (
        <div className="mt-4 rounded-2xl bg-slate-50 p-3 text-sm text-slate-700">
          Streak now at {streakAfter} day{streakAfter === 1 ? "" : "s"}. Keep it going!
        </div>
      )}

      {masteryDeltas.length > 0 && (
        <div className="mt-6 rounded-2xl bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Mastery shifts
          </p>
          <div className="mt-3 space-y-3">
            {masteryDeltas.map((delta) => (
              <div key={delta.skill_id}>
                <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                  <span>{delta.skill_name}</span>
                  <span>
                    {Math.round(delta.old)}% {"->"} {Math.round(delta.new)}%
                  </span>
                </div>
                <MasteryBar value={delta.new} className="mt-1" />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <RunProgress label="Today" value={todayRuns} goal={DAILY_MICROQUEST_GOAL} />
        <RunProgress label="Week" value={weekRuns} goal={WEEKLY_MICROQUEST_GOAL} />
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Button className="flex-1" onClick={onRepeat}>
          <Repeat className="mr-2 h-4 w-4" />
          {ctaLabel ?? "Do another run"}
        </Button>
        <Button className="flex-1" variant="outline" onClick={onBack}>
          <Home className="mr-2 h-4 w-4" />
          Back to Today
        </Button>
        {onOpenSkillMap && (
          <Button className="flex-1" variant="ghost" onClick={onOpenSkillMap}>
            {skillId ? `Skill map: ${skillName ?? "skill"}` : "Open skill map"}
          </Button>
        )}
      </div>
    </div>
  );
}

const SummaryStat = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4 text-center">
    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
    <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
  </div>
);

const RunProgress = ({ label, value, goal }: { label: string; value: number; goal: number }) => {
  const progress = Math.min(1, goal === 0 ? 0 : value / goal);
  return (
    <div className="rounded-2xl border border-slate-100 p-4">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
        <span>{label}</span>
        <span>
          {value} / {goal}
        </span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-slate-100">
        <div
          className="h-2 rounded-full bg-slate-900 transition-all"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
};
