// >>> MEMORY V1 START
import React, { useEffect, useState } from "react";
import { fetchWarmup } from "../api/memory";
import type { ReviewItem } from "../types/memory";
import { WarmupCard } from "../components/WarmupCard";
import { logClient } from "../utils/analytics";

export default function WarmupPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const response = await fetchWarmup(2);
      setItems(response.items);
      logClient("memory.review_shown", { count: response.items.length });
    } catch (error) {
      console.warn("warmup_fetch_failed", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleAnswered = () => {
    void load();
  };

  return (
    <div style={{ maxWidth: 680, margin: "24px auto", padding: 16 }}>
      <h2>Warm-up</h2>
      {loading && <div>Loading warm-up...</div>}
      {!loading && items.length === 0 && <div>No reviews due right now. Check back soon!</div>}
      {!loading &&
        items.map((item) => (
          <WarmupCard key={item.review_card_id} item={item} onAnswered={handleAnswered} />
        ))}
    </div>
  );
}
// <<< MEMORY V1 END
