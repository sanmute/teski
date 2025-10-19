// >>> MEMORY V1 START
import React, { useState } from "react";
import { sendReviewResult } from "../api/memory";
import type { ReviewItem } from "../types/memory";
import { logClient } from "../utils/analytics";

type Props = {
  item: ReviewItem;
  onAnswered: (correct: boolean) => void;
};

export function WarmupCard({ item, onAnswered }: Props) {
  const [pending, setPending] = useState(false);

  const handleAnswer = async (correct: boolean) => {
    if (!item.template_code) {
      onAnswered(correct);
      return;
    }
    try {
      setPending(true);
      logClient("memory.review_answered", {
        template_code: item.template_code,
        correct,
      });
      await sendReviewResult(item.template_code, correct);
    } finally {
      setPending(false);
      onAnswered(correct);
    }
  };

  return (
    <div
      style={{
        border: "1px solid var(--warmup-border, #d9d9d9)",
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ fontWeight: 600 }}>Quick Review</div>
      {item.prompt && <div style={{ opacity: 0.8 }}>{item.prompt}</div>}
      <div style={{ opacity: 0.7, fontSize: 12 }}>
        Template: {item.template_code ?? "unknown"}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button disabled={pending} onClick={() => handleAnswer(true)}>
          I got it ✅
        </button>
        <button disabled={pending} onClick={() => handleAnswer(false)}>
          Still tricky ❌
        </button>
      </div>
    </div>
  );
}
// <<< MEMORY V1 END
