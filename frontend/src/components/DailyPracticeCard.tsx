import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Flame, Target, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  planMicroQuest,
  type MicroQuestPlanResponse,
  getMemoryStats,
  type MemoryStats,
  getBehaviorProfile,
  type BehaviorProfile,
} from "@/api";
import { MasteryBar } from "@/components/MasteryBar";
import { getMicroQuestTodayCount, getMicroQuestWeeklyCount } from "@/lib/microQuestProgress";
import { DAILY_MICROQUEST_GOAL, WEEKLY_MICROQUEST_GOAL } from "@/lib/practiceGoals";

type DailyPracticeCardProps = {
  userId: string;
};

export function DailyPracticeCard({ userId }: DailyPracticeCardProps) {
  const navigate = useNavigate();
  const [plan, setPlan] = useState<MicroQuestPlanResponse | null>(null);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [behavior, setBehavior] = useState<BehaviorProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [todayRuns, setTodayRuns] = useState(() => getMicroQuestTodayCount());
  const [weekRuns, setWeekRuns] = useState(() => getMicroQuestWeeklyCount());

  useEffect(() => {
    const handleRunUpdate = () => {
      setTodayRuns(getMicroQuestTodayCount());
      setWeekRuns(getMicroQuestWeeklyCount());
    };
    window.addEventListener("teski-microquest-run", handleRunUpdate);
    return () => {
      window.removeEventListener("teski-microquest-run", handleRunUpdate);
    };
  }, [userId]);

  const [behaviorLoaded, setBehaviorLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    setBehaviorLoaded(false);
    getBehaviorProfile(userId)
      .then((data) => {
        if (mounted) setBehavior(data);
      })
      .catch(() => {
        if (mounted) setBehavior(null);
      })
      .finally(() => {
        if (mounted) setBehaviorLoaded(true);
      });
    return () => {
      mounted = false;
    };
  }, [userId]);

const [refreshKey, setRefreshKey] = useState(0);

useEffect(() => {
  let cancelled = false;
  const fetchData = async () => {
    if (!behaviorLoaded) return;
    setIsLoading(true);
    try {
      const statsData = await getMemoryStats(userId);
      const suggestedLength = behavior?.suggested_length ?? 5;
      const planData = await planMicroQuest({ user_id: userId, length: suggestedLength });
      if (cancelled) return;
      setPlan(planData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error(err);
      if (!cancelled) setError("Could not load a recommendation right now.");
    } finally {
      if (!cancelled) setIsLoading(false);
    }
  };
  fetchData();
  return () => {
    cancelled = true;
  };
}, [behavior, behaviorLoaded, refreshKey, userId]);

  const masteryValue = Math.round(plan?.mastery ?? 0);
  const suggestedLength = plan?.suggested_length ?? behavior?.suggested_length ?? 5;
  const todayProgress = Math.min(1, todayRuns / DAILY_MICROQUEST_GOAL);
  const weekProgress = Math.min(1, weekRuns / WEEKLY_MICROQUEST_GOAL);

  const baseSubtitle = useMemo(() => {
    if (!plan) return "Micro-quests help keep your streak alive.";
    const reviewRatio =
      plan.items.length === 0
        ? 0
        : plan.items.filter((item) => item.is_review).length / plan.items.length;
    if (reviewRatio >= 0.5) {
      return "Focus on core reviews today to lock them in.";
    }
    return "Push your mastery a little further today.";
  }, [plan]);

  const subtitle = useMemo(() => {
    if (!behavior) return baseSubtitle;
    if (behavior.fatigue_risk >= 70) {
      return "Let's keep it light—short fundamentals runs build confidence.";
    }
    if (behavior.challenge_preference >= 70) {
      return "Ready for a tougher challenge to stretch your skills.";
    }
    if (behavior.review_vs_new_bias >= 70) {
      return "Lean into review mode and lock in recent wins.";
    }
    return baseSubtitle;
  }, [baseSubtitle, behavior]);

  const handleStart = () => {
    const params = new URLSearchParams();
    if (plan?.skill_id) params.set("skill_id", plan.skill_id);
    params.set("len", String(suggestedLength));
    navigate({
      pathname: "/micro-quest",
      search: params.toString(),
    });
  };

  return (
    <div className="mt-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      {isLoading ? (
        <div>
          <Skeleton className="h-5 w-40" />
          <Skeleton className="mt-3 h-7 w-56" />
          <Skeleton className="mt-4 h-3 w-full" />
          <Skeleton className="mt-2 h-3 w-5/6" />
        </div>
      ) : error ? (
        <div className="space-y-3">
          <p className="text-sm text-slate-500">{error}</p>
          <Button variant="outline" onClick={() => setRefreshKey((key) => key + 1)}>
            Retry recommendation
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Daily practice</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-900">
              {plan?.skill_name ? `Sharpen ${plan.skill_name}` : "Start a micro-quest"}
            </h2>
            <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
            <div className="mt-4 flex items-center gap-3 text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <Flame className="h-4 w-4 text-rose-500" />
                <span>Streak: {stats?.streak_days ?? 0} days</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <TrendingUp className="h-4 w-4 text-emerald-500" />
                <span>Mastery: {masteryValue}%</span>
              </div>
            </div>
            <MasteryBar value={masteryValue} className="mt-2" />
            <div className="mt-4 grid gap-4 text-xs text-slate-600 sm:grid-cols-2">
              <div>
                <div className="flex items-center justify-between">
                  <span>Today</span>
                  <span>
                    {todayRuns} / {DAILY_MICROQUEST_GOAL}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-slate-900 transition-all"
                    style={{ width: `${todayProgress * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <span>Week</span>
                  <span>
                    {weekRuns} / {WEEKLY_MICROQUEST_GOAL}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-emerald-500 transition-all"
                    style={{ width: `${weekProgress * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="flex w-full flex-col gap-3 sm:flex-row lg:w-auto">
            <Button className="flex-1" onClick={handleStart}>
              Start {suggestedLength}-question run
            </Button>
            <Button
              className="flex-1"
              variant="outline"
              onClick={() => navigate("/exercises")}
            >
              Explore exercises
            </Button>
          </div>
        </div>
      )}
      <div className="mt-4 flex items-center gap-3 rounded-2xl bg-slate-50 p-3 text-xs text-slate-600">
        <Target className="h-4 w-4 text-slate-400" />
        <span>
          {plan?.review_count ?? 0} review / {plan ? plan.items.length - plan.review_count : 0} challenge
          prompts queued for you.
        </span>
      </div>
    </div>
  );
}
