import React, { useState } from "react";
import { submitFeedback } from "../api/feedback";
import { collectFeedbackContext } from "@/lib/feedback";

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
  const [raffleOptIn, setRaffleOptIn] = useState(false);
  const [raffleName, setRaffleName] = useState("");
  const [raffleEmail, setRaffleEmail] = useState("");

  async function send() {
    if (!message.trim()) return;
    if (raffleOptIn && !raffleName.trim()) {
      setError("Please add your name to join the raffle.");
      return;
    }
    setSending(true);
    setError(null);
    try {
      const context = collectFeedbackContext("floating_feedback", {
        route: typeof window !== "undefined" ? window.location.pathname : undefined,
        user_id: userId,
        source: "floating_feedback",
      });
      await submitFeedback({
        kind,
        severity: kind === "bug" ? severity : undefined,
        message: message.trim(),
        page: context.page,
        page_url: context.page, // backward-compatible field
        user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
        app_version: context.app_version,
        metadata: context.metadata,
        raffle_opt_in: raffleOptIn,
        raffle_name: raffleOptIn ? raffleName.trim() : null,
        raffle_email: raffleOptIn && raffleEmail.trim() ? raffleEmail.trim() : null,
      });
      setSent(true);
      setTimeout(() => {
        setOpen(false);
        setMessage("");
        setRaffleOptIn(false);
        setRaffleName("");
        setRaffleEmail("");
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
      <div className="mt-3 flex items-center gap-2 text-sm">
        <input
          id="raffle-opt-in"
          type="checkbox"
          checked={raffleOptIn}
          onChange={(e) => setRaffleOptIn(e.target.checked)}
          className="h-4 w-4"
        />
        <label htmlFor="raffle-opt-in" className="cursor-pointer">
          I want to participate in the feedback raffle
        </label>
      </div>
      {raffleOptIn && (
        <div className="mt-2 space-y-2 text-sm">
          <div>
            <label className="mb-1 block">Name (required)</label>
            <input
              type="text"
              value={raffleName}
              onChange={(e) => setRaffleName(e.target.value)}
              className="w-full rounded border px-2 py-1"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="mb-1 block">Email (optional)</label>
            <input
              type="email"
              value={raffleEmail}
              onChange={(e) => setRaffleEmail(e.target.value)}
              className="w-full rounded border px-2 py-1"
              placeholder="you@example.com"
            />
          </div>
          <p className="text-xs text-gray-600">Raffle info is used only to contact winners and is not shared.</p>
        </div>
      )}
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
