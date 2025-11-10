import React, { useState } from "react";

type FeedbackButtonProps = {
  userId?: string;
};

export function FeedbackButton({ userId }: FeedbackButtonProps) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  async function send() {
    if (!message.trim()) return;
    setSending(true);
    await fetch("/pilot/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userId ?? null,
        context_json: { path: window.location.pathname },
      }),
    });
    setSending(false);
    setSent(true);
    setTimeout(() => {
      setOpen(false);
      setMessage("");
      setSent(false);
    }, 1200);
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
    <div className="fixed bottom-4 right-4 z-40 w-72 rounded-2xl border bg-white p-4 shadow-2xl">
      <textarea
        className="w-full rounded border p-2 text-sm"
        rows={3}
        placeholder="Tell us what's confusing or great…"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />
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
