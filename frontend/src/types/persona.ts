// >>> PERSONA START
export type PersonaUI = { color: string; emojiSet: string[]; emojiMax: number };
export type PersonaConfig = {
  code: string;
  displayName: string;
  ui: PersonaUI;
  tone: { politeness: string; humor: string; directness: string };
  style: {
    sentenceLength: string;
    emoji: "light" | "moderate" | "party" | "staccato";
    jargon: string;
  };
  reinforcement: { xpMultiplier: number; streakBonus: number; nudges: string[] };
  boundaries: { noCheating: boolean; sensitiveTopicsEscalation: "safe_help" };
  microScripts: Record<string, string[]>;
};
// <<< PERSONA END
