import { useCallback, useEffect, useState } from "react";
import type { UserPrefs } from "@/types/prefs";
import { API_BASE_URL, apiFetch } from "@/api";

function resolvePrefsBase() {
  const customBase = import.meta.env.VITE_PREFS_BASE?.trim();
  if (customBase) {
    const trimmed = customBase.replace(/\/+$/, "");
    return /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  }
  return API_BASE_URL;
}

const PREFS_BASE = resolvePrefsBase();

export function useUserPrefs(userId?: string) {
  const [prefs, setPrefs] = useState<UserPrefs | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await apiFetch<UserPrefs>(`${PREFS_BASE}/prefs/get?user_id=${userId}`);
      if (data) setPrefs(data);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [refresh]);

  return { prefs, loading, refresh };
}
