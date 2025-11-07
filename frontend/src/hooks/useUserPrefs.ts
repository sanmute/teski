import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "@/api";
import type { UserPrefs } from "@/types/prefs";

export function useUserPrefs(userId?: string) {
  const [prefs, setPrefs] = useState<UserPrefs | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/prefs/get?user_id=${userId}`);
      if (res.ok) setPrefs(await res.json());
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    refresh().catch(() => undefined);
  }, [refresh]);

  return { prefs, loading, refresh };
}
