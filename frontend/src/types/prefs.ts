export interface UserPrefs {
  user_id: string;
  allow_llm_feedback: boolean;
  allow_voice_stt: boolean;
  allow_elaboration_prompts: boolean;
  allow_concept_maps: boolean;
  allow_transfer_checks: boolean;
  store_self_explanations: boolean;
  store_concept_maps: boolean;
}
