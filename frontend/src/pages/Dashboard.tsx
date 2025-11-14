import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { fetchUpcomingTasks } from "@/api/tasks";
import { Task } from "@/types/tasks";
import { TaskCard } from "@/components/TaskCard";
import { Button } from "@/components/ui/button";

export default function Dashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchUpcomingTasks();
        setTasks(data.slice(0, 3));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load tasks");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Today&apos;s suggested blocks</h2>
            <p className="text-sm text-muted-foreground">
              Focus on what matters most next.
            </p>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link to="/tasks/upcoming">View all tasks</Link>
          </Button>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading tasks…
          </div>
        )}
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}
        {!loading && !error && tasks.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No tasks yet. Add one to get a personalized plan.
          </p>
        )}
        <div className="grid gap-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </section>

      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold">Quick actions</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Jump into tasks, study profile, or explanations.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/tasks/upcoming">Add a task</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/profile">View study profile</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/help">Explain something</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
