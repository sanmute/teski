// >>> PERSONA START
import React, { useEffect, useState } from "react";
import { listPersonas, previewNudge } from "../api/persona";
import { NudgeCard } from "../components/NudgeCard";

export default function PersonaPreviewPage() {
  const [items, setItems] = useState<{ code: string; displayName: string }[]>([]);
  const [response, setResponse] = useState<Record<string, unknown> | null>(null);
  const [selected, setSelected] = useState<string>("mood_calm_v1");

  useEffect(() => {
    listPersonas().then(setItems).catch(() => {
      setItems([]);
    });
  }, []);

  async function generate() {
    const preview = await previewNudge({
      requestedMood: selected,
      phase: "preTask",
      context: { minutesToDue: 180, overdue: false, repeatedDeferrals: 1 },
    });
    setResponse(preview);
  }

  return (
    <div style={{ maxWidth: 640, margin: "24px auto", padding: 16 }}>
      <h2>Persona Preview</h2>
      <select value={selected} onChange={(event) => setSelected(event.target.value)}>
        {items.map((persona) => (
          <option key={persona.code} value={persona.code}>
            {persona.displayName}
          </option>
        ))}
      </select>
      <button onClick={generate} style={{ marginLeft: 8 }}>
        Preview Nudge
      </button>
      <div style={{ marginTop: 16 }}>
        {response && (
          <NudgeCard
            text={(response.text as string) || ""}
            color={(response.color as string) || "#f5f5f5"}
            persona={(response.persona as string) || ""}
            phase={(response.phase as string) || "preTask"}
          />
        )}
      </div>
    </div>
  );
}
// <<< PERSONA END
