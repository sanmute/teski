import { Task } from "@/types/tasks";

type DemoTasks = {
  upcoming: Task[];
  completed: Task[];
  overdue: Task[];
};

export const demoTasks: DemoTasks = {
  upcoming: [
    {
      id: 101,
      title: "Op-amp lab report (EE230)",
      course: "EE230 · Circuits II",
      kind: "lab",
      due_at: "2026-02-05T15:00:00.000Z",
      status: "pending",
      personalized_estimated_minutes: 95,
      blocks: [
        { id: 1001, task_id: 101, duration_minutes: 30, label: "Data check + plots" },
        { id: 1002, task_id: 101, duration_minutes: 45, label: "Draft discussion" },
        { id: 1003, task_id: 101, duration_minutes: 20, label: "Peer review & polish" },
      ],
    },
    {
      id: 102,
      title: "Signals problem set 4",
      course: "EE240 · Signals & Systems",
      kind: "problem set",
      due_at: "2026-02-06T10:30:00.000Z",
      status: "pending",
      personalized_estimated_minutes: 80,
      blocks: [
        { id: 1004, task_id: 102, duration_minutes: 25, label: "Laplace warm-up" },
        { id: 1005, task_id: 102, duration_minutes: 30, label: "Convolution proofs" },
        { id: 1006, task_id: 102, duration_minutes: 25, label: "Check in with study buddy" },
      ],
    },
    {
      id: 103,
      title: "Data structures quiz prep",
      course: "CS204 · Data Structures",
      kind: "quiz",
      due_at: "2026-02-03T23:00:00.000Z",
      status: "pending",
      personalized_estimated_minutes: 45,
      blocks: [
        { id: 1007, task_id: 103, duration_minutes: 15, label: "Flashcards · trees" },
        { id: 1008, task_id: 103, duration_minutes: 15, label: "Heap practice" },
        { id: 1009, task_id: 103, duration_minutes: 15, label: "Dry-run quiz" },
      ],
    },
  ],
  completed: [
    {
      id: 104,
      title: "Linear algebra flashcards",
      course: "MATH221",
      kind: "review",
      due_at: "2026-02-01T16:00:00.000Z",
      status: "done",
      personalized_estimated_minutes: 30,
      blocks: [
        { id: 1010, task_id: 104, duration_minutes: 15, label: "Eigenvalues drill" },
        { id: 1011, task_id: 104, duration_minutes: 15, label: "SVD intuition" },
      ],
    },
    {
      id: 105,
      title: "Analog filter design sketch",
      course: "EE230 · Circuits II",
      kind: "project",
      due_at: "2026-02-02T18:00:00.000Z",
      status: "done",
      personalized_estimated_minutes: 60,
      blocks: [
        { id: 1012, task_id: 105, duration_minutes: 30, label: "Bode plot review" },
        { id: 1013, task_id: 105, duration_minutes: 30, label: "Peer critique" },
      ],
    },
  ],
  overdue: [
    {
      id: 106,
      title: "Career fair prep notes",
      course: "Professional dev",
      kind: "prep",
      due_at: "2026-01-31T21:00:00.000Z",
      status: "pending",
      personalized_estimated_minutes: 25,
      blocks: [
        { id: 1014, task_id: 106, duration_minutes: 15, label: "Company shortlist" },
        { id: 1015, task_id: 106, duration_minutes: 10, label: "Elevator pitch refresh" },
      ],
    },
  ],
};
