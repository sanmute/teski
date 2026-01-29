import React, { useState } from "react";
import { submitFeedback } from "../api/feedback";

type FeedbackButtonProps = {
  userId?: string;
};

export function FeedbackButton({ userId }: FeedbackButtonProps) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [kind, setKind] = useState<"feedback" | "bug" | "idea">("feedback");
  const [severity, setSeverity] = useState<"low" | "medium" | "high">("medium");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    if (!message.trim()) return;
    setSending(true);
    setError(null);
    try {
      await submitFeedback({
        kind,
        severity: kind === "bug" ? severity : undefined,
        message: message.trim(),
        page_url: window.location.href,
        user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
        app_version: import.meta.env.VITE_APP_VERSION as string | undefined,
        metadata: {
          source: "floating_feedback",
          route: window.location.pathname,
          user_id: userId,
        },
      });
      setSent(true);
      setTimeout(() => {
        setOpen(false);
        setMessage("");
        setSent(false);
      }, 1200);
    } catch (err: any) {
      setError(err?.message || "Could not send feedback");
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <div className="fixed bottom-4 right-4 z-40">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-full bg-black px-4 py-2 text-sm font-medium text-white shadow-lg"
        >
          Feedback
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 w-80 rounded-2xl border bg-white p-4 shadow-2xl">
      <div className="mb-2 flex gap-2">
        {(["feedback", "bug", "idea"] as const).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setKind(k)}
            className={`flex-1 rounded border px-2 py-1 text-sm ${kind === k ? "border-black bg-black text-white" : "border-gray-300"}`}
          >
            {k[0].toUpperCase() + k.slice(1)}
          </button>
        ))}
      </div>
      {kind === "bug" && (
        <div className="mb-2 flex items-center justify-between text-xs text-gray-600">
          <span>Severity</span>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value as typeof severity)}
            className="rounded border px-2 py-1 text-xs"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      )}
      <textarea
        className="w-full rounded border p-2 text-sm"
        rows={3}
        placeholder="Tell us what's confusing or great…"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />
      {error && <div className="mt-1 text-xs text-red-600">{error}</div>}
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={send}
          disabled={sending || sent}
          className="flex-1 rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {sent ? "Sent!" : sending ? "Sending…" : "Send"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="flex-1 rounded bg-gray-200 px-3 py-2 text-sm font-medium text-gray-900"
        >
          Close
        </button>
      </div>
    </div>
  );
}
