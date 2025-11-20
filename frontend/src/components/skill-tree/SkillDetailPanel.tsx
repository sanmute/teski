import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { MasteryBar } from "@/components/MasteryBar";
import type { SkillNodeView } from "./SkillNodeCard";

type SkillDetailPanelProps = {
  open: boolean;
  node: SkillNodeView | null;
  onClose: () => void;
  onStart: (node: SkillNodeView) => void;
  isStarting?: boolean;
};

export function SkillDetailPanel({ open, node, onClose, onStart, isStarting }: SkillDetailPanelProps) {
  return (
    <Dialog open={open} onOpenChange={(value) => (!value ? onClose() : null)}>
      <DialogContent className="max-w-lg">
        {node && (
          <>
            <DialogHeader>
              <DialogTitle>{node.name}</DialogTitle>
              <DialogDescription>{node.description}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-500">
                  <span>Mastery</span>
                  <span>{Math.round(node.mastery)}%</span>
                </div>
                <MasteryBar value={node.mastery} className="mt-1" />
              </div>
              <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                {node.status === "locked" && (
                  <p>
                    Unlock this skill by reinforcing prerequisites:{" "}
                    {node.prerequisites.length > 0 ? node.prerequisites.join(", ") : "Fundamentals"}.
                  </p>
                )}
                {node.status === "in_progress" && (
                  <p>You have momentum here. A focused micro-quest will push it higher.</p>
                )}
                {node.status === "strong" && (
                  <p>Great work! Keep it fresh with a quick mastery check or explore advanced neighbors.</p>
                )}
              </div>
              <Button className="w-full" onClick={() => node && onStart(node)} disabled={isStarting}>
                {isStarting ? "Starting..." : "Start 5-question micro-quest"}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
