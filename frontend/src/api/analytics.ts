import { SummaryMetrics, DailySeries, CourseBreakdown, InsightList } from "@/types/analytics";
import { apiFetch } from "./client";
import { DEMO_MODE } from "@/config/demo";
import { getDemoStats } from "@/demo/state";

export async function fetchMySummary(): Promise<SummaryMetrics> {
  if (DEMO_MODE) {
    return Promise.resolve(getDemoStats().summary);
  }
  return apiFetch<SummaryMetrics>("/analytics/me/summary");
}

export async function fetchMyDaily(days = 14): Promise<DailySeries> {
  if (DEMO_MODE) {
    const stats = getDemoStats();
    return Promise.resolve({
      days: stats.daily.days.slice(-(days ?? stats.daily.days.length)),
    });
  }
  return apiFetch<DailySeries>(`/analytics/me/daily?days=${days}`);
}

export async function fetchMyCourseBreakdown(days = 7): Promise<CourseBreakdown> {
  if (DEMO_MODE) {
    return Promise.resolve(getDemoStats().courses);
  }
  return apiFetch<CourseBreakdown>(`/analytics/me/by-course?days=${days}`);
}

export async function fetchMyInsights(): Promise<InsightList> {
  if (DEMO_MODE) {
    return Promise.resolve(getDemoStats().insights);
  }
  return apiFetch<InsightList>("/analytics/me/insights");
}
