import React, { useCallback, useEffect, useState } from "react";
import { API_BASE } from "@/api";
import type { UserPrefs } from "@/types/prefs";

const defaults: UserPrefs = {
  user_id: "",
  allow_llm_feedback: false,
  allow_voice_stt: false,
  allow_elaboration_prompts: false,
  allow_concept_maps: false,
  allow_transfer_checks: false,
  store_self_explanations: false,
  store_concept_maps: false,
};

export function DeepPrefs({ userId }: { userId: string }) {
  const [prefs, setPrefs] = useState<UserPrefs | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    const res = await fetch(`${API_BASE}/prefs/get?user_id=${userId}`);
    if (res.ok) setPrefs(await res.json());
  }, [userId]);

  useEffect(() => {
    load().catch(() => undefined);
  }, [load]);

  async function save() {
    if (!prefs) return;
    setSaving(true);
    await fetch(`${API_BASE}/prefs/set`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    }).catch(() => undefined);
    setSaving(false);
  }

  const toggle = (key: keyof Omit<UserPrefs, "user_id">) => {
    if (!prefs) return;
    setPrefs({ ...prefs, [key]: !prefs[key] });
  };

  if (!prefs) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground">
        Loading deep-learning preferences…
      </div>
    );
  }

  const current = prefs;

  return (
    <div className="space-y-2 rounded-xl border bg-card p-4 shadow">
      <div>
        <h3 className="font-semibold">Deep-learning pack</h3>
        <p className="text-xs text-muted-foreground">These features are optional and off by default.</p>
      </div>
      <Toggle label="Personalized LLM feedback" value={current.allow_llm_feedback} onToggle={() => toggle("allow_llm_feedback")} />
      <Toggle label="Voice transcription" value={current.allow_voice_stt} onToggle={() => toggle("allow_voice_stt")} />
      <Toggle label="Elaborative prompts" value={current.allow_elaboration_prompts} onToggle={() => toggle("allow_elaboration_prompts")} />
      <Toggle label="Concept maps" value={current.allow_concept_maps} onToggle={() => toggle("allow_concept_maps")} />
      <Toggle label="Transfer checks & calibration" value={current.allow_transfer_checks} onToggle={() => toggle("allow_transfer_checks")} />
      <div className="border-t pt-2 text-sm font-medium">Storage controls</div>
      <Toggle label="Store self-explanations" value={current.store_self_explanations} onToggle={() => toggle("store_self_explanations")} />
      <Toggle label="Store concept maps" value={current.store_concept_maps} onToggle={() => toggle("store_concept_maps")} />
      <button
        onClick={save}
        disabled={saving}
        className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground disabled:opacity-70"
      >
        {saving ? "Saving…" : "Save preferences"}
      </button>
    </div>
  );
}

function Toggle({ label, value, onToggle }: { label: string; value: boolean; onToggle: () => void }) {
  return (
    <label className="flex items-center justify-between text-sm">
      <span>{label}</span>
      <button
        type="button"
        onClick={onToggle}
        className={`rounded px-2 py-1 text-xs font-medium ${value ? "bg-emerald-100 text-emerald-900" : "bg-muted text-muted-foreground"}`}
      >
        {value ? "On" : "Off"}
      </button>
    </label>
  );
}
