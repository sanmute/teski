import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { answerMicroQuestExercise, completeMicroQuest, type ExerciseDTO } from "../api/microquest";

type LocationState = { exercises?: ExerciseDTO[] };

export default function MicroQuestLitePage() {
  const { microquestId } = useParams<{ microquestId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  const exercises = state?.exercises ?? [];

  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const current = exercises[index];

  if (!microquestId || exercises.length === 0) {
    return <div style={{ padding: 24 }}>Missing micro-quest data. Go back to Today and start a new run.</div>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!current) return;
    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      const res = await answerMicroQuestExercise(microquestId, current.id, answer);
      setFeedback(res.correct ? `Correct! ${res.explanation}` : `Not quite. ${res.explanation}`);
      setAnswer("");
    } catch (err: any) {
      setError(err?.message || "Could not submit answer");
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (index + 1 < exercises.length) {
      setIndex(index + 1);
      setFeedback(null);
      setError(null);
      setAnswer("");
      return;
    }
    setLoading(true);
    try {
      const summary = await completeMicroQuest(microquestId);
      navigate(`/practice/micro-quest/${microquestId}/summary`, { state: { summary } });
    } catch (err: any) {
      setError(err?.message || "Could not complete micro-quest");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 24 }}>
      <p style={{ marginBottom: 8 }}>
        Question {index + 1} of {exercises.length}
      </p>
      <h2 style={{ fontSize: 22, marginBottom: 12 }}>{current.prompt}</h2>
      <form onSubmit={handleSubmit}>
        {current.type === "mcq" && current.choices && (
          <div style={{ marginBottom: 12 }}>
            {current.choices.map((choice) => (
              <label key={choice} style={{ display: "block", marginBottom: 6 }}>
                <input
                  type="radio"
                  name="answer"
                  value={choice}
                  checked={answer === choice}
                  onChange={(e) => setAnswer(e.target.value)}
                  required
                />{" "}
                {choice}
              </label>
            ))}
          </div>
        )}
        {current.type !== "mcq" && (
          <div style={{ marginBottom: 12 }}>
            <input
              type="text"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer"
              required
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
            />
          </div>
        )}
        {error && <div style={{ color: "#e11d48", marginBottom: 8 }}>{error}</div>}
        {feedback && <div style={{ marginBottom: 8 }}>{feedback}</div>}
        <button
          type="submit"
          disabled={loading}
          style={{ padding: "10px 16px", borderRadius: 8, border: "none", background: "#0f172a", color: "white", fontWeight: 600 }}
        >
          {loading ? "Checking..." : "Check answer"}
        </button>
      </form>
      {feedback && (
        <button
          onClick={handleNext}
          disabled={loading}
          style={{ marginTop: 12, padding: "10px 16px", borderRadius: 8, border: "1px solid #cbd5e1", background: "white" }}
        >
          {index + 1 < exercises.length ? "Next question" : "Finish"}
        </button>
      )}
    </div>
  );
}
