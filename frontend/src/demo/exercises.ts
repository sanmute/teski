type DemoExerciseType = "MCQ" | "NUMERIC" | "SHORT";

export type DemoExercise = {
  id: string;
  question_text: string;
  type: DemoExerciseType;
  choices?: { id: string; text: string }[];
  correct_answer: string | number;
  difficulty: number;
  skill_ids: string[];
  hint?: string;
  solution_explanation?: string;
  metadata?: Record<string, unknown>;
};

export const demoExercises: DemoExercise[] = [
  {
    id: "ex-demo-1",
    question_text: "What does the quality factor (Q) of a band-pass filter represent?",
    type: "MCQ",
    choices: [
      { id: "a", text: "Ratio of stored to dissipated energy per cycle" },
      { id: "b", text: "Total power delivered by the source" },
      { id: "c", text: "Cutoff frequency minus center frequency" },
      { id: "d", text: "Filter order" },
    ],
    correct_answer: "a",
    difficulty: 2,
    skill_ids: ["signals", "filters"],
    hint: "Think about how sharply the filter rings at resonance.",
    solution_explanation: "Q compares stored to lost energy each cycle; high Q means narrow bandwidth and slow decay.",
    metadata: { concept: "Resonance", tags: ["filters", "bandwidth"] },
  },
  {
    id: "ex-demo-2",
    question_text: "For a BJT biased at 0.2 mA with β=120, what is the approximate base current?",
    type: "NUMERIC",
    correct_answer: 0.0017,
    difficulty: 3,
    skill_ids: ["electronics", "devices"],
    hint: "Ic ≈ β * Ib.",
    solution_explanation: "Ib ≈ Ic/β = 0.2 mA / 120 ≈ 0.00167 mA.",
    metadata: { unit: "mA", tolerance: 0.0002 },
  },
  {
    id: "ex-demo-3",
    question_text: "Explain why convolution in time corresponds to multiplication in the frequency domain.",
    type: "SHORT",
    correct_answer: "because the Fourier transform of a convolution is the product of transforms",
    difficulty: 4,
    skill_ids: ["signals", "fourier"],
    hint: "Recall the convolution theorem.",
    solution_explanation: "The convolution theorem states F{x*y} = F{x}·F{y}, so convolving time signals multiplies spectra.",
    metadata: { target: "convolution theorem" },
  },
  {
    id: "ex-demo-4",
    question_text: "Which data structure offers O(log n) insertion and O(1) access to min element?",
    type: "MCQ",
    choices: [
      { id: "a", text: "Binary min-heap" },
      { id: "b", text: "Hash map" },
      { id: "c", text: "AVL tree" },
      { id: "d", text: "Queue" },
    ],
    correct_answer: "a",
    difficulty: 1,
    skill_ids: ["cs", "data-structures"],
    hint: "Think priority queues.",
    solution_explanation: "A binary min-heap keeps the smallest element at the root with O(log n) inserts and O(1) min lookup.",
    metadata: { course: "CS204" },
  },
  {
    id: "ex-demo-5",
    question_text: "If |H(jω)| peaks at 1 kHz with -3 dB points at 800 Hz and 1.25 kHz, what is the bandwidth?",
    type: "NUMERIC",
    correct_answer: 450,
    difficulty: 3,
    skill_ids: ["signals", "filters"],
    hint: "Bandwidth = f_high - f_low.",
    solution_explanation: "1.25 kHz - 0.8 kHz = 0.45 kHz (450 Hz).",
    metadata: { unit: "Hz" },
  },
];
