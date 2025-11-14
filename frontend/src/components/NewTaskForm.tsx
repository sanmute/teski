import { useState } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Task } from "@/types/tasks";
import { createTask, TaskCreatePayload } from "@/api/tasks";

interface NewTaskFormProps {
  onCreated?: (task: Task) => void;
  onCancel?: () => void;
}

const KIND_OPTIONS = [
  { value: "homework", label: "Homework" },
  { value: "exam", label: "Exam" },
  { value: "reading", label: "Reading" },
  { value: "other", label: "Other" },
];

export function NewTaskForm({ onCreated, onCancel }: NewTaskFormProps) {
  const [title, setTitle] = useState("");
  const [course, setCourse] = useState("");
  const [kind, setKind] = useState<string | undefined>("homework");
  const [dueDate, setDueDate] = useState("");
  const [dueTime, setDueTime] = useState("");
  const [baseMinutes, setBaseMinutes] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildPayload = (): TaskCreatePayload => {
    let due_at: string | null = null;
    if (dueDate) {
      const time = dueTime || "23:59";
      const iso = new Date(`${dueDate}T${time}`).toISOString();
      due_at = iso;
    }
    return {
      title: title.trim(),
      course: course.trim() || null,
      kind: kind || null,
      due_at,
      base_estimated_minutes: Math.max(5, Number(baseMinutes) || 5),
    };
  };

  const handleSubmit = async (evt: React.FormEvent) => {
    evt.preventDefault();
    if (!title.trim()) {
      setError("Please enter a task title.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = buildPayload();
      const task = await createTask(payload);
      onCreated?.(task);
      setTitle("");
      setCourse("");
      setKind("homework");
      setDueDate("");
      setDueTime("");
      setBaseMinutes(60);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="space-y-2">
        <Label htmlFor="task-title">Title *</Label>
        <Input
          id="task-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Mechanics problem set"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="task-course">Course</Label>
        <Input
          id="task-course"
          value={course}
          onChange={(e) => setCourse(e.target.value)}
          placeholder="Physics 1"
        />
      </div>

      <div className="space-y-2">
        <Label>Kind</Label>
        <Select value={kind} onValueChange={setKind}>
          <SelectTrigger>
            <SelectValue placeholder="Choose kind" />
          </SelectTrigger>
          <SelectContent>
            {KIND_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="task-date">Due date</Label>
          <Input
            id="task-date"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="task-time">Due time</Label>
          <Input
            id="task-time"
            type="time"
            value={dueTime}
            onChange={(e) => setDueTime(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="task-minutes">Estimated minutes *</Label>
        <Input
          id="task-minutes"
          type="number"
          min={5}
          value={baseMinutes}
          onChange={(e) => setBaseMinutes(Number(e.target.value))}
        />
        <p className="text-xs text-muted-foreground">
          Teski will adjust this based on your usual estimation pattern.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex items-center justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create task"}
        </Button>
      </div>
    </form>
  );
}
