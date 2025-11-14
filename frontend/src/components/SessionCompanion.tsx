import React from "react";

import type { CharacterId } from "@/types/characters";
import { useSessionCompanion, SessionPhase } from "@/hooks/useSessionCompanion";

interface SessionCompanionProps {
  phase: SessionPhase;
  elapsedMinutes: number;
  character: CharacterId;
}

export const SessionCompanion: React.FC<SessionCompanionProps> = ({ phase, elapsedMinutes, character }) => {
  const { line } = useSessionCompanion(phase, elapsedMinutes, character);
  const charIndex = character.replace("character", "");

  return (
    <div className="flex items-start gap-3 rounded-xl border bg-ts-secondary/40 p-3 shadow-sm">
      <div
        className="flex h-12 w-12 items-center justify-center rounded-full bg-ts-primary text-sm font-semibold text-white shadow-[0_0_12px_0_var(--ts-glow)]"
        aria-label={`Character ${charIndex}`}
      >
        #{charIndex}
      </div>
      <div className="flex-1">
        <div className="inline-block max-w-full rounded-2xl bg-ts-accent px-3 py-2 text-sm text-slate-900 shadow-sm">
          {line || "I’ll keep you company while you work."}
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {phase === "prepare" && "Preparing this block."}
          {phase === "focus" && "Focused work in progress."}
          {phase === "close" && "Wrapping up and reflecting."}
        </p>
      </div>
    </div>
  );
};
