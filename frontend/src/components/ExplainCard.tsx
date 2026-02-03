import React, { useRef, useState } from "react";
import { API_BASE } from "@/api";
import { DEMO_MODE } from "@/config/demo";

type ExplainResp = {
  score_deep: number;
  rubric: Record<string, unknown>;
  next_prompts: { prompts?: string[] };
};

interface Props {
  userId: string;
  topicId: string;
  enabled?: boolean;
}

export function ExplainCard({ userId, topicId, enabled = true }: Props) {
  const [text, setText] = useState("");
  const [resp, setResp] = useState<ExplainResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function submit(mode: "text" | "voice", payloadText?: string) {
    if (!payloadText && !text.trim()) return;
    if (DEMO_MODE) {
      setResp({
        score_deep: 82,
        rubric: {},
        next_prompts: { prompts: ["Can you draw the main diagram?", "Where does intuition break?", "Name one real device it applies to."] },
      });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/deep/explain/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          topic_id: topicId,
          mode,
          text: payloadText ?? text,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResp(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to evaluate explanation");
    } finally {
      setLoading(false);
    }
  }

  async function transcribeAndSubmit() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    if (DEMO_MODE) {
      setResp({
        score_deep: 78,
        rubric: {},
        next_prompts: { prompts: ["Summarize the signal flow in one sentence.", "What would fail first if you doubled the load?"] },
      });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_BASE}/deep/explain/transcribe?user_id=${userId}`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      await submit("voice", data.text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed");
      setLoading(false);
    }
  }

  if (!enabled) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground">
        Self-explanations are off. Enable LLM feedback + storage in Settings.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border bg-card p-4 shadow">
      <h3 className="font-semibold">Explain it back (Feynman check)</h3>
      <textarea
        className="w-full rounded border bg-background p-2 text-sm"
        rows={4}
        placeholder="Explain the concept in your own words…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
      />
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => submit("text")}
          className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground disabled:opacity-70"
          disabled={loading || !text.trim()}
        >
          {loading ? "Evaluating…" : "Evaluate"}
        </button>
        <input ref={fileRef} type="file" accept="audio/*" className="text-xs" disabled={loading} />
        <button
          onClick={transcribeAndSubmit}
          className="rounded bg-muted px-3 py-1 text-sm disabled:opacity-70"
          disabled={loading}
        >
          Use voice file
        </button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {resp && (
        <div className="space-y-1 rounded bg-muted/60 p-3 text-sm">
          <div>
            Depth score: <span className="font-semibold">{resp.score_deep}</span>/100
          </div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">Next prompts</div>
          <ul className="ml-4 list-disc">
            {(resp.next_prompts?.prompts ?? []).map((prompt, idx) => (
              <li key={idx}>{prompt}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
