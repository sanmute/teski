// >>> PERSONA START
import React from "react";

type Props = {
  text: string;
  color: string;
  persona: string;
  phase: string;
};

export function NudgeCard({ text, color, persona, phase }: Props) {
  const style: React.CSSProperties = color.startsWith("linear-gradient")
    ? { backgroundImage: color, color: "#111", borderRadius: 12, padding: 12 }
    : { background: color, color: "#111", borderRadius: 12, padding: 12 };
  return (
    <div style={style} aria-live="polite">
      <div style={{ fontSize: 12, opacity: 0.7 }}>
        {persona} • {phase}
      </div>
      <div style={{ fontSize: 16, marginTop: 4 }}>{text}</div>
    </div>
  );
}
// <<< PERSONA END
