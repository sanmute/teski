import { useEffect, useState } from "react";
import { Loader2, AlertCircle, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Task } from "@/types/tasks";
import { fetchUpcomingTasks, markTaskDone } from "@/api/tasks";
import { startStudySession } from "@/api/study";
import { TaskCard } from "@/components/TaskCard";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { NewTaskForm } from "@/components/NewTaskForm";
import { useToast } from "@/hooks/use-toast";
import { MoodleIntegration } from "@/components/MoodleIntegration";

export default function TasksUpcoming() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showNewTask, setShowNewTask] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUpcomingTasks();
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleMarkDone = async (taskId: number) => {
    try {
      await markTaskDone(taskId);
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status: "done" } : task)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadTasks();
    setRefreshing(false);
  };

  const handleStartSession = async (_taskId: number, blockId: number) => {
    try {
      const session = await startStudySession(blockId);
      toast({
        title: "Session ready",
        description: "Follow the adaptive plan to finish this block.",
      });
      navigate(`/study/session/${session.session_id}`);
    } catch (err) {
      toast({
        title: "Could not start session",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold">Upcoming tasks</h1>
            <p className="text-sm text-muted-foreground">
              These tasks are broken into study blocks based on your profile.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing || loading}>
              {refreshing ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Refreshing…
                </span>
              ) : (
                "Refresh"
              )}
            </Button>
            <Button size="sm" onClick={() => setShowNewTask(true)}>
              <Plus className="h-4 w-4 mr-1" />
              New task
            </Button>
          </div>
        </header>

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading tasks…
          </div>
        )}

        <MoodleIntegration
          onImported={() => {
            setRefreshing(true);
            loadTasks().finally(() => setRefreshing(false));
          }}
        />

        {error && !loading && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && tasks.length === 0 && (
          <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
            No upcoming tasks yet. Add one to see personalized blocks here.
          </div>
        )}

        <div className="space-y-4">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onStatusChange={handleMarkDone}
              onStartSession={handleStartSession}
            />
          ))}
        </div>
      </div>

      <Dialog open={showNewTask} onOpenChange={setShowNewTask}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Create a new task</DialogTitle>
            <DialogDescription>Add a task and we’ll build a personalized plan for it.</DialogDescription>
          </DialogHeader>
          <NewTaskForm
            onCreated={(task) => {
              setTasks((prev) => [task, ...prev]);
              setShowNewTask(false);
            }}
            onCancel={() => setShowNewTask(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
