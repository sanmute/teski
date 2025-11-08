import React from "react";
import { Link } from "react-router-dom";
import { ExplainCard } from "@/components/ExplainCard";
import { ConceptMapWidget } from "@/components/ConceptMapWidget";
import { CalibrationChip } from "@/components/CalibrationChip";
import { useUserPrefs } from "@/hooks/useUserPrefs";
import { DEMO_TOPIC_ID, DEMO_USER_ID } from "@/lib/constants";

const DEMO_ITEM_ID = "item-demo-123";

export default function DeepLearningLab() {
  const { prefs, loading } = useUserPrefs(DEMO_USER_ID);
  const allowExplain = !!(prefs?.allow_llm_feedback && prefs?.store_self_explanations);
  const allowConcept = !!(prefs?.allow_concept_maps && prefs?.store_concept_maps);
  const allowCalibration = !!prefs?.allow_transfer_checks;

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Deep Learning Lab</h1>
          <p className="text-sm text-muted-foreground">
            Optional tools for deeper learning. Toggle features in Settings.
          </p>
        </div>
        <Link to="/" className="text-sm font-medium text-primary underline-offset-2 hover:underline">
          ← Back to dashboard
        </Link>
      </div>
      {loading && <p className="text-sm text-muted-foreground">Loading preferences…</p>}
      <ExplainCard userId={DEMO_USER_ID} topicId={DEMO_TOPIC_ID} enabled={allowExplain} />
      <ConceptMapWidget userId={DEMO_USER_ID} topicId={DEMO_TOPIC_ID} enabled={allowConcept} />
      <div className="rounded-xl border bg-card p-4">
        <h3 className="mb-2 font-semibold">Confidence calibration</h3>
        <CalibrationChip
          userId={DEMO_USER_ID}
          itemId={DEMO_ITEM_ID}
          topicId={DEMO_TOPIC_ID}
          enabled={allowCalibration}
        />
        {!allowCalibration && (
          <p className="text-xs text-muted-foreground">
            Turn on transfer checks in Settings to log confidence.
          </p>
        )}
      </div>
    </div>
  );
}
