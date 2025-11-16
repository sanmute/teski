export interface SummaryMetrics {
  today_minutes: number;
  today_blocks: number;
  week_minutes: number;
  week_blocks: number;
  streak_days: number;
}

export interface DailyPoint {
  date: string;
  minutes: number;
  blocks: number;
}

export interface DailySeries {
  days: DailyPoint[];
}

export interface CourseBreakdownItem {
  course_id: string | null;
  course_name: string;
  minutes: number;
  blocks: number;
  on_track: boolean | null;
}

export interface CourseBreakdown {
  items: CourseBreakdownItem[];
}

export type InsightSeverity = "info" | "warning" | "critical";

export type InsightCategory =
  | "consistency"
  | "balance"
  | "workload"
  | "timing"
  | "focus";

export interface Insight {
  id: string;
  severity: InsightSeverity;
  category: InsightCategory;
  title: string;
  message: string;
}

export interface InsightList {
  insights: Insight[];
}
