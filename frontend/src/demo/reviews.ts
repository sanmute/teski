import { MemoryNext } from "@/api";

type DemoMistake = {
  concept: string;
  note: string;
  last_seen: string;
};

type DemoRecommended = {
  concept: string;
  reason: string;
  due_in_minutes: number;
};

export const demoReviews: {
  queue: MemoryNext[];
  mistakes: DemoMistake[];
  recommended: DemoRecommended[];
} = {
  queue: [
    {
      memory_id: "mem-101",
      concept: "Laplace transform ROIs",
      due_at: "2026-02-03T15:10:00.000Z",
    },
    {
      memory_id: "mem-102",
      concept: "Op-amp saturation limits",
      due_at: "2026-02-03T16:45:00.000Z",
    },
    {
      memory_id: "mem-103",
      concept: "Binary heap invariants",
      due_at: "2026-02-03T18:00:00.000Z",
    },
    {
      memory_id: "mem-104",
      concept: "BJT small-signal model",
      due_at: "2026-02-04T09:00:00.000Z",
    },
  ],
  mistakes: [
    {
      concept: "Convolution step responses",
      note: "Mixed up time reversal in last attempt; revisit diagram.",
      last_seen: "2026-01-31",
    },
    {
      concept: "Bias point drift",
      note: "Forgot to include temperature coefficient in calculation.",
      last_seen: "2026-02-01",
    },
  ],
  recommended: [
    { concept: "Complex impedance intuition", reason: "recent hint usage", due_in_minutes: 35 },
    { concept: "AVL rotations", reason: "2 incorrect in a row", due_in_minutes: 80 },
  ],
};
