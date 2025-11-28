import { api } from "./client";

export type ExerciseDTO = {
  id: string;
  prompt: string;
  type: string;
  choices?: string[] | null;
};

export type MicroQuestStartResponse = {
  microquest_id: string;
  exercises: ExerciseDTO[];
};

export type MicroQuestAnswerResponse = {
  correct: boolean;
  explanation: string;
};

export type MicroQuestCompleteResponse = {
  microquest_id: string;
  correct_count: number;
  total_count: number;
  accuracy: number;
  debrief: Record<string, unknown>;
};

export async function startMicroQuest(): Promise<MicroQuestStartResponse> {
  return api.post<MicroQuestStartResponse>("/ex/micro-quest/start", {});
}

export async function answerMicroQuestExercise(
  microquestId: string,
  exerciseId: string,
  answer: string,
): Promise<MicroQuestAnswerResponse> {
  return api.post<MicroQuestAnswerResponse>(`/ex/micro-quest/${microquestId}/answer`, {
    exercise_id: exerciseId,
    answer,
  });
}

export async function completeMicroQuest(microquestId: string): Promise<MicroQuestCompleteResponse> {
  return api.post<MicroQuestCompleteResponse>(`/ex/micro-quest/${microquestId}/complete`, {});
}
