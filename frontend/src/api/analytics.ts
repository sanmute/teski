import {
  SummaryMetrics,
  DailySeries,
  CourseBreakdown,
  InsightList,
} from "@/types/analytics";
import { apiFetch } from "./client";

export async function fetchMySummary(): Promise<SummaryMetrics> {
  return apiFetch<SummaryMetrics>("/analytics/me/summary");
}

export async function fetchMyDaily(days = 14): Promise<DailySeries> {
  return apiFetch<DailySeries>(`/analytics/me/daily?days=${days}`);
}

export async function fetchMyCourseBreakdown(days = 7): Promise<CourseBreakdown> {
  return apiFetch<CourseBreakdown>(`/analytics/me/by-course?days=${days}`);
}

export async function fetchMyInsights(): Promise<InsightList> {
  return apiFetch<InsightList>("/analytics/me/insights");
}
