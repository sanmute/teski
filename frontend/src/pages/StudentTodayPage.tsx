import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { startMicroQuest } from "../api/microquest";
import { DEMO_MODE } from "@/config/demo";
import { demoToday } from "@/demo/today";
import { getDemoTasksSnapshot } from "@/demo/state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function StudentTodayPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localTasks, setLocalTasks] = useState(
    () => (DEMO_MODE ? getDemoTasksSnapshot().upcoming.slice(0, 2) : []),
  );

  const focusPlan = useMemo(() => demoToday, []);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await startMicroQuest();
      navigate(`/practice/micro-quest/${data.microquest_id}`, { state: { exercises: data.exercises } });
    } catch (err: any) {
      setError(err?.message || "Could not start practice");
    } finally {
      setLoading(false);
    }
  };

  if (DEMO_MODE) {
    return (
      <div className="mx-auto flex max-w-4xl flex-col gap-6 rounded-xl border bg-card p-6">
        <header className="space-y-1">
          <p className="text-xs uppercase tracking-wide text-primary">Demo day</p>
          <h1 className="text-2xl font-semibold">Today&apos;s plan</h1>
          <p className="text-sm text-muted-foreground">{focusPlan.focus}</p>
        </header>

        <section className="rounded-lg border bg-muted/30 p-4">
          <h2 className="text-sm font-semibold">Quick steps</h2>
          <ul className="mt-3 space-y-2 text-sm text-foreground">
            {localTasks.map((task) => (
              <li key={task.id} className="flex items-center justify-between rounded-md bg-background px-3 py-2">
                <div>
                  <p className="font-medium">{task.title}</p>
                  <p className="text-xs text-muted-foreground">{task.course}</p>
                </div>
                <Button
                  size="sm"
                  variant={task.status === "done" ? "secondary" : "outline"}
                  onClick={() =>
                    setLocalTasks((prev) =>
                      prev.map((t) => (t.id === task.id ? { ...t, status: t.status === "done" ? "pending" : "done" } : t)),
                    )
                  }
                >
                  {task.status === "done" ? "Completed" : "Mark done"}
                </Button>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">{focusPlan.suggestion}</p>
        </section>

        <section className="rounded-lg border p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold">Warm up with 3 exercises</h3>
              <p className="text-xs text-muted-foreground">
                No logins or backend — instant demo answers.
              </p>
            </div>
            <Button onClick={() => navigate("/exercises")}>Open exercises</Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary">Signals</Badge>
            <Badge variant="secondary">Circuits II</Badge>
            <Badge variant="secondary">Data structures</Badge>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 24 }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Today</h1>
      <p style={{ marginBottom: 16 }}>Kick off a short practice run to warm up.</p>
      {error && <div style={{ color: "#e11d48", marginBottom: 12 }}>{error}</div>}
      <button
        onClick={handleStart}
        disabled={loading}
        style={{
          padding: "12px 18px",
          borderRadius: 10,
          border: "none",
          background: "#0f172a",
          color: "white",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        {loading ? "Starting..." : "Start practice"}
      </button>
    </div>
  );
}
