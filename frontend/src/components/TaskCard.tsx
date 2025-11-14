import { format } from "date-fns";
import { CheckCircle2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Task, TaskStatus } from "@/types/tasks";
import { cn } from "@/lib/utils";

interface TaskCardProps {
  task: Task;
  onStatusChange?: (taskId: number, status: TaskStatus) => void;
}

export function TaskCard({ task, onStatusChange }: TaskCardProps) {
  const dueLabel = task.due_at ? format(new Date(task.due_at), "EEE dd.MM, HH:mm") : null;
  const isDone = task.status === "done";

  const handleMarkDone = () => {
    if (isDone) return;
    onStatusChange?.(task.id, "done");
  };

  return (
    <Card className={cn("flex flex-col gap-4 p-4 transition", isDone && "opacity-60")}>
      <CardHeader className="p-0">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-lg font-semibold">{task.title}</CardTitle>
            {task.course && <p className="text-sm text-muted-foreground">{task.course}</p>}
          </div>
          <div className="flex items-center gap-2">
            {task.kind && (
              <Badge variant="secondary" className="uppercase tracking-wide text-[0.65rem]">
                {task.kind}
              </Badge>
            )}
            {isDone && (
              <Badge variant="outline" className="flex items-center gap-1 text-emerald-600 border-emerald-300">
                <CheckCircle2 className="h-3 w-3" />
                Completed
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground">
          {dueLabel && <span>Due {dueLabel}</span>}
          <span className="font-medium text-foreground">
            ~{task.personalized_estimated_minutes} min total
          </span>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
            Study blocks
          </p>
          <div className="flex flex-wrap gap-2">
            {task.blocks.map((block) => (
              <div
                key={block.id}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs shadow-sm",
                  block.label.toLowerCase().includes("starter") && "bg-amber-50 border-amber-200",
                  block.label.toLowerCase().includes("focus") && "bg-sky-50 border-sky-200",
                  block.label.toLowerCase().includes("review") && "bg-emerald-50 border-emerald-200"
                )}
              >
                {block.label} · {block.duration_minutes} min
              </div>
            ))}
            {task.blocks.length === 0 && (
              <span className="text-xs text-muted-foreground">No blocks generated</span>
            )}
          </div>
        </div>

        <div className="flex justify-end">
          {isDone ? (
            <span className="text-xs font-medium text-emerald-600">Well done!</span>
          ) : (
            <Button size="sm" variant="outline" onClick={handleMarkDone}>
              Mark as done
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
