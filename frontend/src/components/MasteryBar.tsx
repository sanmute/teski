import { cn } from "@/lib/utils";

type MasteryBarProps = {
  value: number;
  className?: string;
};

export function MasteryBar({ value, className }: MasteryBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const color =
    clamped >= 70 ? "bg-emerald-500" : clamped >= 40 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className={cn("w-full rounded-full bg-slate-100 p-0.5", className)}>
      <div
        className={cn("h-2 rounded-full transition-all", color)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
