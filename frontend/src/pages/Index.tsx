import { useEffect, useMemo, useState } from "react";
import { TaskCard } from "@/components/TaskCard";
import { SettingsPanel } from "@/components/SettingsPanel";
import { MoodleIntegration } from "@/components/MoodleIntegration";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Task } from "@/types/task";
import { Calendar, Upload } from "lucide-react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import { Loader2, RefreshCcw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import clsx from "clsx";
import { CompanionCharacter } from "@/components/PetFrog";
import { AppLogo } from "@/components/AppLogo";
import { DEMO_USER_ID } from "@/lib/constants";

interface IndexProps {
  onTriggerFrog?: (urgency: 'calm' | 'snark' | 'disappointed' | 'intervention' | 'done', message: string) => void;
  companion: CompanionCharacter;
  onCompanionChange: (companion: CompanionCharacter) => void;
}

export default function Index({ onTriggerFrog, companion, onCompanionChange }: IndexProps) {
  const [demoMode, setDemoMode] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: tasks = [], isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["tasks"],
    queryFn: api.getTasks,
  });

  useEffect(() => {
    if (tasks.length > 0 && demoMode) {
      setDemoMode(false);
    }
  }, [tasks.length, demoMode]);

  const markDoneMutation = useMutation({
    mutationFn: api.markTaskDone,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
    onError: (err: unknown) =>
      toast({
        title: "Failed to mark task done",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      }),
  });

  const undoMutation = useMutation({
    mutationFn: api.undoTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
    onError: (err: unknown) =>
      toast({
        title: "Failed to undo task",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      }),
  });

  const { overdueTasks, activeTasks, completedTasks } = useMemo(() => {
    const hasTasks = tasks.length > 0;
    const source = demoMode && !hasTasks
      ? ([
          {
            id: "demo-1",
            source: "mock",
            title: "Linear Algebra HW 2",
            due_iso: "2025-09-17T23:59:00+03:00",
            status: "open",
            priority: 2,
          },
          {
            id: "demo-2",
            source: "mock",
            title: "Mechanical Engineering Lab Report",
            due_iso: "2025-09-14T18:00:00+03:00",
            status: "overdue",
            priority: 3,
          },
        ] as Task[])
      : tasks;

    const now = new Date();
    const overdue: Task[] = [];
    const active: Task[] = [];
    const completed: Task[] = [];

    source.forEach((task) => {
      if (task.status === 'done') {
        completed.push(task);
        return;
      }

      if (task.status === 'overdue') {
        const dueDate = new Date(task.due_iso);
        const diffHours = (now.getTime() - dueDate.getTime()) / (1000 * 60 * 60);
        if (diffHours <= 36) {
          overdue.push(task);
        }
      } else {
        active.push(task);
      }
    });

    overdue.sort((a, b) => new Date(a.due_iso).getTime() - new Date(b.due_iso).getTime());
    active.sort((a, b) => new Date(a.due_iso).getTime() - new Date(b.due_iso).getTime());
    completed.sort((a, b) => new Date(b.completed_at ?? b.due_iso).getTime() - new Date(a.completed_at ?? a.due_iso).getTime());

    return { overdueTasks: overdue, activeTasks: active, completedTasks: completed };
  }, [demoMode, tasks]);

  const importIcsMutation = useMutation({
    mutationFn: api.importIcsFile,
    onSuccess: (result) => {
      toast({
        title: "ICS imported",
        description: `Imported ${result.imported}, updated ${result.updated}, skipped ${result.skipped}.`,
      });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      refetch();
      setDemoMode(false);
    },
    onError: (err: unknown) => {
      toast({
        title: "Import failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  const handleIcsImport = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".ics";
    input.onchange = (event) => {
      const files = (event.target as HTMLInputElement).files;
      if (!files || files.length === 0) return;
      importIcsMutation.mutate(files[0]);
    };
    input.click();
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div className="text-center flex-1 space-y-4">
            <AppLogo />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary-glow bg-clip-text text-transparent">
              Deadline Shamer Dashboard
            </h1>
            <p className="text-muted-foreground text-lg mt-2">
              Because procrastination deserves consequences
            </p>
          </div>
          <SettingsPanel 
            demoMode={demoMode}
            onDemoModeChange={setDemoMode}
            companion={companion}
            onCompanionChange={onCompanionChange}
            userId={DEMO_USER_ID}
          />
        </div>

        {/* Moodle Integration */}
        <MoodleIntegration
          onImported={() => {
            setDemoMode(false);
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            refetch();
          }}
        />
        
        {/* Tasks Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-foreground flex items-center gap-2">
              Your Tasks of Shame
              <span className="text-lg">💀</span>
            </h2>

            <Button 
              variant="outline" 
              className="flex items-center gap-2 hover:shadow-glow transition-smooth"
              onClick={handleIcsImport}
              disabled={importIcsMutation.isPending}
            >
              <Calendar className="w-4 h-4" />
              <Upload className="w-4 h-4" />
              {importIcsMutation.isPending ? "Importing…" : "Import ICS Calendar"}
            </Button>
          </div>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {tasks.length === 0
                ? (demoMode ? 'Demo mode enabled (showing sample tasks).' : 'No data yet — import an ICS file.')
                : 'Live data from backend.'}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant={demoMode ? "default" : "outline"}
                size="sm"
                onClick={() => setDemoMode((val) => !val)}
                disabled={tasks.length > 0}
              >
                {demoMode ? 'Disable demo mode' : (tasks.length > 0 ? 'Demo disabled (live data)' : 'Enable demo mode')}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => refetch()}
                disabled={isFetching}
                className="flex items-center gap-1"
              >
                <RefreshCcw className={clsx("w-4 h-4", isFetching && "animate-spin")} />
                Refresh
              </Button>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <Link to="/deep" className="underline-offset-2 hover:underline">
                  Deep learning lab
                </Link>
                <Link to="/admin/costs" className="underline-offset-2 hover:underline">
                  Admin panel
                </Link>
              </div>
            </div>
          </div>
          
          {isLoading ? (
            <div className="flex items-center justify-center h-48 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading tasks…
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center h-48 text-destructive space-y-2">
              <p>Failed to load tasks. Is the backend running on :8000?</p>
              <Button size="sm" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          ) : (overdueTasks.length + activeTasks.length === 0) ? (
            <div className="flex items-center justify-center h-48 text-muted-foreground">
              No tasks yet. Import an ICS file or create one via the API.
            </div>
          ) : (
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-4">
                {overdueTasks.length > 0 && (
                  <section className="space-y-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold uppercase tracking-wide text-destructive">
                        Overdue (past 7 days)
                      </h3>
                      <span className="text-xs text-destructive/80">Handle these first</span>
                    </div>
                    <div className="space-y-3">
                      {overdueTasks.map((task: Task) => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          companion={companion}
                          onTriggerFrog={onTriggerFrog}
                          onMarkDone={(id) => markDoneMutation.mutate(id)}
                          onUndo={(id) => undoMutation.mutate(id)}
                          disabled={markDoneMutation.isPending || undoMutation.isPending}
                        />
                      ))}
                    </div>
                  </section>
                )}

                <section className="space-y-3 rounded-lg border border-primary/20 bg-card/40 p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground/80">
                    Active tasks
                  </h3>
                  <div className="space-y-3">
                    {activeTasks.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No active tasks right now. Enjoy the calm!</p>
                    ) : (
                      activeTasks.map((task: Task) => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          companion={companion}
                          onTriggerFrog={onTriggerFrog}
                          onMarkDone={(id) => markDoneMutation.mutate(id)}
                          onUndo={(id) => undoMutation.mutate(id)}
                          disabled={markDoneMutation.isPending || undoMutation.isPending}
                        />
                      ))
                    )}
                  </div>
                </section>

                {completedTasks.length > 0 && (
                  <section className="space-y-3 rounded-lg border border-muted/40 bg-muted/10 p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                        Completed tasks
                      </h3>
                      <span className="text-xs text-muted-foreground/80">Great job 🙌</span>
                    </div>
                    <div className="space-y-3 opacity-80">
                      {completedTasks.map((task: Task) => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          companion={companion}
                          onTriggerFrog={onTriggerFrog}
                          onMarkDone={(id) => markDoneMutation.mutate(id)}
                          onUndo={(id) => undoMutation.mutate(id)}
                          disabled={markDoneMutation.isPending || undoMutation.isPending}
                        />
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </ScrollArea>
          )}
        </div>
      </div>
    </div>
  );
};
