import {
  SummaryMetrics,
  DailySeries,
  CourseBreakdown,
  InsightList,
} from "@/types/analytics";
import { getClientUserId } from "@/lib/user";
import { apiFetch } from "./client";

export async function fetchMySummary(): Promise<SummaryMetrics> {
  return apiFetch<SummaryMetrics>("/analytics/me/summary", {
    headers: { "X-User-Id": getClientUserId() },
  });
}

export async function fetchMyDaily(days = 14): Promise<DailySeries> {
  return apiFetch<DailySeries>(`/analytics/me/daily?days=${days}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
}

export async function fetchMyCourseBreakdown(days = 7): Promise<CourseBreakdown> {
  return apiFetch<CourseBreakdown>(`/analytics/me/by-course?days=${days}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
}

export async function fetchMyInsights(): Promise<InsightList> {
  return apiFetch<InsightList>("/analytics/me/insights", {
    headers: { "X-User-Id": getClientUserId() },
  });
}
