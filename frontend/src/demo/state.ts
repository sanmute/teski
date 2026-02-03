import { demoUser } from "./demoUser";
import { demoTasks } from "./tasks";
import { demoExercises, type DemoExercise } from "./exercises";
import { demoReviews } from "./reviews";
import { demoSummary, demoDaily, demoCourses, demoInsights, demoStatsExtras } from "./stats";
import { demoProfile } from "./profile";
import type { Task } from "@/types/tasks";
import type { SummaryMetrics, DailySeries, CourseBreakdown, InsightList } from "@/types/analytics";

type TaskCreateShape = {
  title: string;
  course?: string | null;
  kind?: string | null;
  due_at?: string | null;
  base_estimated_minutes: number;
};

const tasksState: { upcoming: Task[]; completed: Task[]; overdue: Task[] } = {
  upcoming: demoTasks.upcoming.map((task) => ({ ...task, blocks: task.blocks.map((b) => ({ ...b })) })),
  completed: demoTasks.completed.map((task) => ({ ...task, blocks: task.blocks.map((b) => ({ ...b })) })),
  overdue: demoTasks.overdue.map((task) => ({ ...task, blocks: task.blocks.map((b) => ({ ...b })) })),
};

const exercisesState: Record<
  string,
  DemoExercise & { completed?: boolean; lastCorrect?: boolean; attempts?: number }
> = demoExercises.reduce((acc, ex) => {
  acc[ex.id] = { ...ex };
  return acc;
}, {} as Record<string, DemoExercise & { completed?: boolean; lastCorrect?: boolean; attempts?: number }>);

const reviewsState = {
  queue: demoReviews.queue.map((item) => ({ ...item })),
};

const statsState = {
  summary: { ...demoSummary },
  daily: { days: demoDaily.days.map((d) => ({ ...d })) } as DailySeries,
  courses: { items: demoCourses.items.map((c) => ({ ...c })) } as CourseBreakdown,
  insights: { insights: demoInsights.insights.map((i) => ({ ...i })) } as InsightList,
  extras: { ...demoStatsExtras, exercisesCompleted: demoStatsExtras.exercisesCompleted, accuracy: demoStatsExtras.accuracy },
  correctAttempts: Math.round(demoStatsExtras.exercisesCompleted * demoStatsExtras.accuracy),
};

const profileState = { ...demoProfile };

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}

export function getDemoUser() {
  return { ...demoUser };
}

export function getDemoTasksSnapshot() {
  return deepClone(tasksState);
}

export function markDemoTaskDone(taskId: number) {
  const collections = [tasksState.upcoming, tasksState.overdue];
  for (const list of collections) {
    const task = list.find((t) => t.id === taskId);
    if (task) {
      task.status = "done";
      tasksState.completed.unshift({ ...task });
      return deepClone(task);
    }
  }
  return null;
}

export function addDemoTask(payload: TaskCreateShape): Task {
  const newId = Date.now() % 100000;
  const blocks = [
    {
      id: newId * 10 + 1,
      task_id: newId,
      duration_minutes: Math.max(15, Math.round(payload.base_estimated_minutes * 0.4)),
      label: "Warm-up pass",
    },
    {
      id: newId * 10 + 2,
      task_id: newId,
      duration_minutes: Math.max(15, Math.round(payload.base_estimated_minutes * 0.35)),
      label: "Deep work",
    },
  ];
  const task: Task = {
    id: newId,
    title: payload.title,
    course: payload.course ?? null ?? undefined,
    kind: payload.kind ?? undefined,
    due_at: payload.due_at ?? null ?? undefined,
    status: "pending",
    personalized_estimated_minutes: Math.max(20, payload.base_estimated_minutes),
    blocks,
  };
  tasksState.upcoming.unshift(task);
  return deepClone(task);
}

export function getDemoExercisesList() {
  return Object.values(exercisesState).map((ex) => ({
    id: ex.id,
    concept: ex.question_text,
    type: ex.type,
    difficulty: ex.difficulty,
    tags: Array.isArray(ex.metadata?.tags) ? (ex.metadata?.tags as string[]) : undefined,
  }));
}

export function getDemoExerciseById(id: string) {
  const ex = exercisesState[id];
  if (!ex) return null;
  return {
    id: ex.id,
    concept: ex.question_text,
    prompt: ex.question_text,
    type: ex.type,
    difficulty: ex.difficulty,
    choices: ex.choices,
    unit_hint: typeof ex.metadata?.unit === "string" ? (ex.metadata.unit as string) : undefined,
    hint: ex.hint,
    max_xp: 40,
  };
}

export function submitDemoExerciseAnswer(exerciseId: string, answer: unknown) {
  const ex = exercisesState[exerciseId];
  if (!ex) {
    return {
      correct: false,
      xp_awarded: 0,
      persona_msg: "Could not find that exercise.",
    };
  }

  const attempts = (ex.attempts ?? 0) + 1;
  ex.attempts = attempts;

  const normalizedAnswer =
    typeof answer === "object" && answer !== null && "answer" in (answer as Record<string, unknown>)
      ? (answer as Record<string, unknown>).answer
      : answer;

  const correct =
    typeof ex.correct_answer === "number"
      ? Math.abs(Number(normalizedAnswer) - Number(ex.correct_answer)) < 1e-3 ||
        Math.abs(Number(normalizedAnswer) - Number(ex.correct_answer)) <= Number(ex.metadata?.tolerance ?? 0.05)
      : String(normalizedAnswer).trim().toLowerCase() === String(ex.correct_answer).trim().toLowerCase();

  ex.completed = true;
  ex.lastCorrect = correct;

  statsState.extras.exercisesCompleted += 1;
  statsState.correctAttempts += correct ? 1 : 0;
  const attempted = Math.max(statsState.extras.exercisesCompleted, statsState.correctAttempts);
  statsState.extras.accuracy = Math.max(0, Math.min(1, statsState.correctAttempts / attempted));

  statsState.summary.today_blocks = Math.max(statsState.summary.today_blocks, 2);
  statsState.summary.today_minutes += 10;
  statsState.summary.week_minutes += 10;

  const response = {
    correct,
    xp_awarded: correct ? 35 : 10,
    persona_msg: correct ? "Nice — you nailed it!" : "Logged for review. Keep at it.",
    explanation: ex.solution_explanation,
  };

  return response;
}

export function getDemoReviewQueue() {
  return deepClone(reviewsState.queue);
}

export function gradeDemoReview() {
  const item = reviewsState.queue.shift();
  if (!item) {
    return {
      persona_msg: "All clear for today!",
      xp_awarded: 0,
    };
  }
  statsState.summary.today_blocks += 1;
  statsState.extras.exercisesCompleted += 1;
  statsState.correctAttempts += 1;
  statsState.extras.accuracy = Math.max(0, Math.min(1, statsState.correctAttempts / statsState.extras.exercisesCompleted));
  return {
    persona_msg: `Good recall on ${item.concept}`,
    xp_awarded: 12,
  };
}

export function getDemoStats() {
  return {
    summary: deepClone(statsState.summary) as SummaryMetrics,
    daily: deepClone(statsState.daily) as DailySeries,
    courses: deepClone(statsState.courses) as CourseBreakdown,
    insights: deepClone(statsState.insights) as InsightList,
    extras: { ...statsState.extras },
  };
}

export function getDemoProfile() {
  return deepClone(profileState);
}

export function updateDemoProfile(patch: Partial<typeof profileState>) {
  Object.assign(profileState, patch);
  return getDemoProfile();
}

export function resetDemoQueue() {
  reviewsState.queue = demoReviews.queue.map((item) => ({ ...item }));
}
