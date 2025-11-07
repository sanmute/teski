import React, { useState } from "react";
import { API_BASE } from "@/api";

interface Props {
  userId: string;
  itemId: string;
  topicId: string;
  onLogged?: () => void;
  enabled?: boolean;
}

export function CalibrationChip({ userId, itemId, topicId, onLogged, enabled = true }: Props) {
  const [confidence, setConfidence] = useState(3);
  const [submitting, setSubmitting] = useState(false);

  async function log(correct: boolean) {
    if (!enabled) return;
    setSubmitting(true);
    await fetch(`${API_BASE}/deep/confidence/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        item_id: itemId,
        topic_id: topicId,
        confidence,
        correct,
      }),
    }).catch(() => undefined);
    setSubmitting(false);
    onLogged?.();
  }

  if (!enabled) {
    return <div className="text-xs text-muted-foreground">Transfer checks are disabled.</div>;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-muted-foreground">Confidence</span>
      <select
        value={confidence}
        onChange={(e) => setConfidence(Number(e.target.value))}
        className="rounded border bg-background px-2 py-1 text-sm"
        disabled={submitting}
      >
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
      <button
        onClick={() => log(true)}
        className="rounded bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-900 disabled:opacity-70"
        disabled={submitting}
      >
        Correct
      </button>
      <button
        onClick={() => log(false)}
        className="rounded bg-rose-100 px-2 py-1 text-xs font-medium text-rose-900 disabled:opacity-70"
        disabled={submitting}
      >
        Wrong
      </button>
    </div>
  );
}
