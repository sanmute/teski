import { cn } from "@/lib/utils";
import type { PersonaReaction } from "@/api";

type PersonaReactionBubbleProps = {
  reaction?: PersonaReaction | null;
  className?: string;
};

const personaStyles: Record<string, { bg: string; text: string; accent: string }> = {
  calm: { bg: "bg-sky-50 border-sky-100", text: "text-sky-900", accent: "text-sky-500" },
  snark: { bg: "bg-purple-50 border-purple-100", text: "text-purple-900", accent: "text-purple-500" },
  hype: { bg: "bg-emerald-50 border-emerald-100", text: "text-emerald-900", accent: "text-emerald-500" },
  professor: { bg: "bg-slate-50 border-slate-200", text: "text-slate-900", accent: "text-slate-500" },
};

export function PersonaReactionBubble({ reaction, className }: PersonaReactionBubbleProps) {
  if (!reaction) return null;
  const style = personaStyles[reaction.persona] ?? personaStyles.calm;

  return (
    <div
      className={cn(
        "mt-4 rounded-2xl border px-4 py-3 text-sm shadow-sm transition-all",
        style.bg,
        className,
      )}
    >
      <p className={cn("font-medium", style.text)}>{reaction.message}</p>
      <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
        <span className={cn("capitalize font-semibold", style.accent)}>{reaction.persona}</span>
        <span>{reaction.mood}</span>
        <span className="uppercase tracking-wide">{reaction.intensity}</span>
      </div>
    </div>
  );
}
