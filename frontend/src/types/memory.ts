// >>> MEMORY V1 START
export type ReviewItem = {
  type: "review";
  review_card_id: number;
  template_code?: string;
  instance_id?: number;
  prompt?: string;
};

export type WarmupResponse = {
  items: ReviewItem[];
};
// <<< MEMORY V1 END
