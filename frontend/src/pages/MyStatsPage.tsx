import { useEffect, useMemo, useState } from "react";
import {
  fetchMyCourseBreakdown,
  fetchMyDaily,
  fetchMyInsights,
  fetchMySummary,
} from "@/api/analytics";
import type {
  CourseBreakdownItem,
  DailyPoint,
  Insight,
  SummaryMetrics,
} from "@/types/analytics";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

const MIN_DAILY_DAYS = 14;
const COURSE_RANGE_DAYS = 7;

export const MyStatsPage = () => {
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [daily, setDaily] = useState<DailyPoint[]>([]);
  const [courses, setCourses] = useState<CourseBreakdownItem[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, dailyRes, coursesRes, insightsRes] = await Promise.all([
          fetchMySummary(),
          fetchMyDaily(MIN_DAILY_DAYS),
          fetchMyCourseBreakdown(COURSE_RANGE_DAYS),
          fetchMyInsights(),
        ]);

        if (!isMounted) return;
        setSummary(summaryRes);
        setDaily(dailyRes.days ?? []);
        setCourses(coursesRes.items ?? []);
        setInsights(insightsRes.insights ?? []);
      } catch (err) {
        console.error(err);
        if (isMounted) {
          setError("Failed to load stats");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, []);

  const totalCourseMinutes = useMemo(
    () => courses.reduce((sum, course) => sum + course.minutes, 0),
    [courses],
  );

  const hasDailyData = daily.length > 0 && daily.some((day) => day.minutes > 0);

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">My Stats</h1>
        <p className="text-sm text-muted-foreground">
          See how your recent focus time stacks up.
        </p>
      </header>

      {loading && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Skeleton className="h-24 rounded-xl" />
            <Skeleton className="h-24 rounded-xl" />
            <Skeleton className="h-24 rounded-xl" />
          </div>
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && summary && (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Today
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <p className="text-2xl font-semibold">
                  {summary.today_minutes} min
                </p>
                <p className="text-xs text-muted-foreground">
                  {summary.today_blocks} focus block
                  {summary.today_blocks === 1 ? "" : "s"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  This week
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <p className="text-2xl font-semibold">
                  {summary.week_minutes} min
                </p>
                <p className="text-xs text-muted-foreground">
                  {summary.week_blocks} focus block
                  {summary.week_blocks === 1 ? "" : "s"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Streak
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <p className="text-2xl font-semibold">
                  {summary.streak_days} day
                  {summary.streak_days === 1 ? "" : "s"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Consecutive days with logged focus time
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold">
                  Last {MIN_DAILY_DAYS} days
                </CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                {hasDailyData ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={daily}>
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value: string) => value.slice(5)}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        width={40}
                        allowDecimals={false}
                      />
                      <Tooltip
                        formatter={(value: number, name: string) =>
                          name === "minutes" ? `${value} min` : value
                        }
                        labelFormatter={(label: string) => `Date: ${label}`}
                        contentStyle={{
                          borderRadius: "0.5rem",
                          borderColor: "hsl(var(--border))",
                        }}
                      />
                      <Bar
                        dataKey="minutes"
                        radius={[4, 4, 0, 0]}
                        fill="hsl(var(--primary))"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    No sessions logged yet. Start a study block to see your
                    streak grow.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-semibold">
                  Recent pattern
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>
                  Track how many minutes you&apos;ve invested each day and look
                  for consistency over peaks. Small, frequent blocks tend to
                  beat marathon cramming sessions.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">
                By course (last {COURSE_RANGE_DAYS} days)
              </h2>
              <p className="text-xs text-muted-foreground">
                Where your study time went.
              </p>
            </div>

            <Card>
              <CardContent className="divide-y">
                {courses.length === 0 && (
                  <p className="py-4 text-sm text-muted-foreground">
                    No recent study sessions. Once you start a few blocks,
                    course insights will appear here.
                  </p>
                )}

                {courses.map((course) => {
                  const pct =
                    totalCourseMinutes > 0
                      ? Math.round((course.minutes / totalCourseMinutes) * 100)
                      : 0;

                  return (
                    <div
                      key={course.course_id ?? course.course_name}
                      className="flex flex-col gap-1 py-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium">
                            {course.course_name || "Unassigned"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {course.minutes} min · {course.blocks} block
                            {course.blocks === 1 ? "" : "s"}
                          </p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {pct}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-muted">
                        <div
                          className="h-1.5 rounded-full bg-primary"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Insights</h2>
              <p className="text-xs text-muted-foreground">
                Short observations based on recent study patterns.
              </p>
            </div>

            <Card>
              <CardContent className="space-y-3 py-4">
                {insights.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No specific insights yet. As you log more study sessions,
                    we&apos;ll highlight notable patterns here.
                  </p>
                )}

                {insights.map((insight) => (
                  <div
                    key={insight.id}
                    className="flex flex-col gap-1 rounded-lg border border-slate-200/80 bg-card px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium">{insight.title}</h3>
                      <div className="flex items-center gap-1">
                        <span
                          className={`
                            inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium
                            ${
                              insight.severity === "critical"
                                ? "bg-red-100 text-red-700"
                                : insight.severity === "warning"
                                  ? "bg-amber-100 text-amber-700"
                                  : "bg-sky-100 text-sky-700"
                            }
                          `}
                        >
                          {insight.severity === "critical"
                            ? "Critical"
                            : insight.severity === "warning"
                              ? "Warning"
                              : "Info"}
                        </span>
                        <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700">
                          {insight.category}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600">{insight.message}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </div>
  );
};

export default MyStatsPage;
