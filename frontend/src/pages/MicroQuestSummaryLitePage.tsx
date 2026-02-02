import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { type MicroQuestCompleteResponse } from "../api/microquest";
import { submitFeedback } from "../api/feedback";
import { collectFeedbackContext } from "@/lib/feedback";

type LocationState = { summary?: MicroQuestCompleteResponse };

export default function MicroQuestSummaryLitePage() {
  const { microquestId } = useParams<{ microquestId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  const summary = state?.summary;

  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackRating, setFeedbackRating] = useState<number | undefined>(undefined);
  const [feedbackStatus, setFeedbackStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [raffleOptIn, setRaffleOptIn] = useState(false);
  const [raffleName, setRaffleName] = useState("");
  const [raffleEmail, setRaffleEmail] = useState("");

  if (!summary || !microquestId) {
    return <div style={{ padding: 24 }}>Summary missing. Start a new micro-quest from Today.</div>;
  }

  const message =
    typeof summary.debrief?.message === "string" ? summary.debrief.message : JSON.stringify(summary.debrief);

  const handleSendFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackMessage.trim()) return;
    if (raffleOptIn && !raffleName.trim()) {
      setFeedbackError("Name is required to join the raffle.");
      setFeedbackStatus("error");
      return;
    }
    setFeedbackStatus("sending");
    setFeedbackError(null);
    try {
      const context = collectFeedbackContext("microquest_summary", {
        rating: feedbackRating,
        context: "microquest_summary",
        route: `/practice/micro-quest/${microquestId}/summary`,
      });
      await submitFeedback({
        kind: "feedback",
        severity: undefined,
        message: feedbackMessage.trim(),
        page: context.page,
        page_url: context.page, // backward-compatible field
        app_version: context.app_version,
        metadata: context.metadata,
        raffle_opt_in: raffleOptIn,
        raffle_name: raffleOptIn ? raffleName.trim() : null,
        raffle_email: raffleOptIn && raffleEmail.trim() ? raffleEmail.trim() : null,
      });
      setFeedbackStatus("sent");
    } catch (err: any) {
      setFeedbackStatus("error");
      setFeedbackError(err?.message || "Failed to send feedback");
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 24 }}>
      <h1 style={{ fontSize: 26, marginBottom: 12 }}>Session summary</h1>
      <p>
        You answered {summary.correct_count} out of {summary.total_count} correctly.
      </p>
      <p>Accuracy: {(summary.accuracy * 100).toFixed(0)}%</p>
      <h2 style={{ marginTop: 16, marginBottom: 8 }}>Debrief</h2>
      <p>{message}</p>
      <section style={{ marginTop: 24, padding: 16, border: "1px solid #e2e8f0", borderRadius: 12 }}>
        <h3 style={{ marginBottom: 8 }}>How did this session feel?</h3>
        <p style={{ marginBottom: 12 }}>Share a quick note so we can improve.</p>
        <form onSubmit={handleSendFeedback}>
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: "block", marginBottom: 4 }}>Your feedback</label>
            <textarea
              value={feedbackMessage}
              onChange={(e) => setFeedbackMessage(e.target.value)}
              rows={3}
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
              placeholder="What worked? What felt off?"
            />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: "block", marginBottom: 4 }}>Overall rating</label>
            <div style={{ display: "flex", gap: 6 }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setFeedbackRating(star)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 8,
                    border: feedbackRating === star ? "2px solid #0f172a" : "1px solid #cbd5e1",
                    background: feedbackRating === star ? "#e2e8f0" : "#fff",
                    cursor: "pointer",
                  }}
                >
                  {star}
                </button>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={raffleOptIn}
                onChange={(e) => setRaffleOptIn(e.target.checked)}
              />
              <span>I want to participate in the feedback raffle</span>
            </label>
            {raffleOptIn && (
              <div style={{ marginTop: 8 }}>
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "block", marginBottom: 4 }}>Name (required)</label>
                  <input
                    type="text"
                    value={raffleName}
                    onChange={(e) => setRaffleName(e.target.value)}
                    placeholder="Your name"
                    style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                  />
                </div>
                <div style={{ marginBottom: 8 }}>
                  <label style={{ display: "block", marginBottom: 4 }}>Email (optional)</label>
                  <input
                    type="email"
                    value={raffleEmail}
                    onChange={(e) => setRaffleEmail(e.target.value)}
                    placeholder="you@example.com"
                    style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                  />
                </div>
                <p style={{ fontSize: 12, color: "#475569" }}>
                  Raffle info is used only to contact winners and is not shared.
                </p>
              </div>
            )}
          </div>
          {feedbackError && <div style={{ color: "#e11d48", marginBottom: 8 }}>{feedbackError}</div>}
          {feedbackStatus === "sent" ? (
            <div style={{ color: "#16a34a", marginBottom: 8 }}>Thanks for the feedback!</div>
          ) : (
            <button
              type="submit"
              disabled={feedbackStatus === "sending" || !feedbackMessage.trim()}
              style={{
                padding: "10px 16px",
                borderRadius: 8,
                border: "none",
                background: "#0f172a",
                color: "white",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {feedbackStatus === "sending" ? "Sending..." : "Send feedback"}
            </button>
          )}
        </form>
      </section>
      <button
        onClick={() => navigate("/today")}
        style={{ marginTop: 16, padding: "10px 16px", borderRadius: 8, border: "1px solid #cbd5e1", background: "white" }}
      >
        Back to Today
      </button>
    </div>
  );
}
