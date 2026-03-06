import { api } from "./client";

export type ExamResult = {
  course_code: string;
  course_name: string;
  department: string;
  date: string;
  pdf_url: string;
  has_exams: boolean;
  exam_count: number;
  exam_pdf_urls: string[];
};

export type CourseSearchResponse = {
  query: string;
  results: ExamResult[];
  total_found: number;
};

export type GeneratedExerciseOut = {
  id: string;
  concept: string;
  type: string;
  question: string;
  difficulty: number;
  skill_ids: string[];
  keywords: string[];
  course: string | null;
  domain: string | null;
  meta: Record<string, unknown>;
  explanation: string;
  raw_markdown: string;
};

export type PipelineResponse = {
  course_name: string;
  exercises: GeneratedExerciseOut[];
  pdf_count: number;
  source_urls: string[];
};

export type SaveResponse = {
  saved: string[];
  skipped: string[];
};

export async function searchCourses(query: string): Promise<CourseSearchResponse> {
  return api.get<CourseSearchResponse>(
    `/exam-pipeline/search?q=${encodeURIComponent(query)}`
  );
}

export async function generateFromExams(payload: {
  course_name: string;
  course_code?: string;
  pdf_urls: string[];
  num_exercises?: number;
  exercise_types?: string[];
  difficulty_min?: number;
  difficulty_max?: number;
}): Promise<PipelineResponse> {
  return api.post<PipelineResponse>("/exam-pipeline/generate", payload);
}

export async function saveExercises(
  exercises: GeneratedExerciseOut[]
): Promise<SaveResponse> {
  return api.post<SaveResponse>("/exam-pipeline/save", { exercises });
}
