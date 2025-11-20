import { MasteryBar } from "@/components/MasteryBar";
import { cn } from "@/lib/utils";

export type SkillStatus = "locked" | "in_progress" | "strong";

export type SkillNodeView = {
  id: string;
  name: string;
  description: string;
  category: string;
  mastery: number;
  status: SkillStatus;
  depth: number;
  prerequisites: string[];
  children: string[];
  recommended: boolean;
};

const STATUS_CONFIG: Record<
  SkillStatus,
  { label: string; bg: string; border: string; badge: string }
> = {
  locked: {
    label: "Locked",
    bg: "bg-slate-50",
    border: "border-slate-200",
    badge: "bg-slate-200 text-slate-600",
  },
  in_progress: {
    label: "In progress",
    bg: "bg-blue-50",
    border: "border-blue-200",
    badge: "bg-blue-100 text-blue-700",
  },
  strong: {
    label: "Strong",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    badge: "bg-emerald-100 text-emerald-700",
  },
};

type SkillNodeCardProps = {
  node: SkillNodeView;
  onSelect: (node: SkillNodeView) => void;
};

export function SkillNodeCard({ node, onSelect }: SkillNodeCardProps) {
  const config = STATUS_CONFIG[node.status];
  return (
    <button
      type="button"
      onClick={() => onSelect(node)}
      className={cn(
        "w-full rounded-2xl border p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/40",
        config.bg,
        config.border,
        node.recommended && "ring-2 ring-slate-900/30",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-slate-900">{node.name}</p>
        <span className={cn("rounded-full px-2 py-0.5 text-xs font-semibold", config.badge)}>
          {config.label}
        </span>
      </div>
      <p className="mt-1 line-clamp-2 text-xs text-slate-600">{node.description}</p>
      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Mastery</span>
          <span>{Math.round(node.mastery)}%</span>
        </div>
        <MasteryBar value={node.mastery} className="mt-1" />
      </div>
      {node.recommended && (
        <p className="mt-3 text-xs font-medium text-slate-700">Suggested focus</p>
      )}
    </button>
  );
}
