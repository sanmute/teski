import { CourseBreakdown, DailySeries, InsightList, SummaryMetrics } from "@/types/analytics";

export const demoSummary: SummaryMetrics = {
  today_minutes: 55,
  today_blocks: 2,
  week_minutes: 310,
  week_blocks: 9,
  streak_days: 12,
};

export const demoDaily: DailySeries = {
  days: [
    { date: "2026-01-22", minutes: 20, blocks: 1 },
    { date: "2026-01-23", minutes: 35, blocks: 2 },
    { date: "2026-01-24", minutes: 50, blocks: 2 },
    { date: "2026-01-25", minutes: 0, blocks: 0 },
    { date: "2026-01-26", minutes: 40, blocks: 1 },
    { date: "2026-01-27", minutes: 60, blocks: 2 },
    { date: "2026-01-28", minutes: 45, blocks: 2 },
    { date: "2026-01-29", minutes: 30, blocks: 1 },
    { date: "2026-01-30", minutes: 55, blocks: 2 },
    { date: "2026-01-31", minutes: 25, blocks: 1 },
    { date: "2026-02-01", minutes: 40, blocks: 2 },
    { date: "2026-02-02", minutes: 70, blocks: 2 },
    { date: "2026-02-03", minutes: 55, blocks: 2 },
    { date: "2026-02-04", minutes: 0, blocks: 0 },
  ],
};

export const demoCourses: CourseBreakdown = {
  items: [
    { course_id: "EE230", course_name: "Circuits II", minutes: 120, blocks: 4, on_track: true },
    { course_id: "EE240", course_name: "Signals & Systems", minutes: 95, blocks: 3, on_track: true },
    { course_id: "CS204", course_name: "Data Structures", minutes: 60, blocks: 2, on_track: false },
    { course_id: "MATH221", course_name: "Linear Algebra", minutes: 35, blocks: 1, on_track: true },
  ],
};

export const demoInsights: InsightList = {
  insights: [
    {
      id: "insight-1",
      severity: "info",
      category: "consistency",
      title: "Streak is building momentum",
      message: "You’ve studied 12 days in a row. Keep sessions short to extend it through midterms.",
    },
    {
      id: "insight-2",
      severity: "warning",
      category: "balance",
      title: "Data Structures needs time",
      message: "CS204 blocks dipped below 90 minutes this week. Add one 20-minute heap drill tomorrow.",
    },
    {
      id: "insight-3",
      severity: "info",
      category: "timing",
      title: "Evening focus works",
      message: "Most high-output blocks happened after 18:00. Protect that slot for exam prep.",
    },
  ],
};

export const demoStatsExtras = {
  exercisesCompleted: 186,
  accuracy: 0.88,
  weakAreas: ["Laplace transforms", "AVL rotations", "BJT bias stability"],
  charts: {
    accuracyTrend: [
      { label: "Week -2", value: 0.83 },
      { label: "Week -1", value: 0.86 },
      { label: "This week", value: 0.88 },
    ],
  },
};
