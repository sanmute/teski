import {
  SummaryMetrics,
  DailySeries,
  CourseBreakdown,
  InsightList,
} from "@/types/analytics";
import { getClientUserId } from "@/lib/user";

export async function fetchMySummary(): Promise<SummaryMetrics> {
  const res = await fetch("/analytics/me/summary", {
    headers: { "X-User-Id": getClientUserId() },
  });
  if (!res.ok) {
    throw new Error("Failed to load summary");
  }
  return res.json();
}

export async function fetchMyDaily(days = 14): Promise<DailySeries> {
  const res = await fetch(`/analytics/me/daily?days=${days}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
  if (!res.ok) {
    throw new Error("Failed to load daily series");
  }
  return res.json();
}

export async function fetchMyCourseBreakdown(days = 7): Promise<CourseBreakdown> {
  const res = await fetch(`/analytics/me/by-course?days=${days}`, {
    headers: { "X-User-Id": getClientUserId() },
  });
  if (!res.ok) {
    throw new Error("Failed to load course breakdown");
  }
  return res.json();
}

export async function fetchMyInsights(): Promise<InsightList> {
  const res = await fetch("/analytics/me/insights", {
    headers: { "X-User-Id": getClientUserId() },
  });
  if (!res.ok) {
    throw new Error("Failed to load insights");
  }
  return res.json();
}
