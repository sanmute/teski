export type ExplanationStyle =
  | "step_by_step"
  | "big_picture"
  | "analogy"
  | "visual"
  | "problems";

export interface ExplanationBlock {
  style: ExplanationStyle;
  title?: string;
  content: string;
}

export interface ExplanationResponse {
  chosen_style: ExplanationStyle;
  blocks: ExplanationBlock[];
}
