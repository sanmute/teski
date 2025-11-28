import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { startMicroQuest } from "../api/microquest";

export default function StudentTodayPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await startMicroQuest();
      navigate(`/practice/micro-quest/${data.microquest_id}`, { state: { exercises: data.exercises } });
    } catch (err: any) {
      setError(err?.message || "Could not start practice");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 24 }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Today</h1>
      <p style={{ marginBottom: 16 }}>Kick off a short practice run to warm up.</p>
      {error && <div style={{ color: "#e11d48", marginBottom: 12 }}>{error}</div>}
      <button
        onClick={handleStart}
        disabled={loading}
        style={{
          padding: "12px 18px",
          borderRadius: 10,
          border: "none",
          background: "#0f172a",
          color: "white",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        {loading ? "Starting..." : "Start practice"}
      </button>
    </div>
  );
}
