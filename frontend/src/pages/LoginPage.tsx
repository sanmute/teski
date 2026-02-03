import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { login, signup } from "../api/auth";
import { DEMO_MODE } from "@/config/demo";
import { demoUser } from "@/demo/demoUser";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: Location } };
  const from = location.state?.from?.pathname || "/today";

  useEffect(() => {
    if (DEMO_MODE) {
      navigate(from, { replace: true });
    }
  }, [from, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(email, password);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  if (DEMO_MODE) {
    return (
      <div style={{ maxWidth: 420, margin: "60px auto", padding: "24px", border: "1px solid #e2e8f0", borderRadius: 12 }}>
        <h1 style={{ fontSize: 28, marginBottom: 8 }}>Teski</h1>
        <p style={{ marginBottom: 16 }}>Demo mode is active.</p>
        <p style={{ fontSize: 14, lineHeight: 1.5 }}>
          You&apos;re already signed in as <strong>{demoUser.name}</strong>. Head to Today or Tasks to explore the
          demo experience.
        </p>
        <button
          style={{ marginTop: 16, padding: 10, width: "100%", borderRadius: 10, border: "none", background: "#0f172a", color: "white", fontWeight: 600 }}
          onClick={() => navigate(from, { replace: true })}
        >
          Go to app
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "24px", border: "1px solid #e2e8f0", borderRadius: 12 }}>
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>Teski</h1>
      <p style={{ marginBottom: 16 }}>{mode === "login" ? "Log in to practice" : "Create an account"}</p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 4 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", marginBottom: 4 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </div>
        {error && <div style={{ color: "#e11d48", marginBottom: 8 }}>{error}</div>}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 10,
            border: "none",
            background: "#0f172a",
            color: "white",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {loading ? "Please wait..." : mode === "login" ? "Log in" : "Sign up"}
        </button>
      </form>
      <button
        type="button"
        onClick={() => setMode(mode === "login" ? "signup" : "login")}
        style={{ marginTop: 12, width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1", background: "white" }}
      >
        {mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
      </button>
    </div>
  );
}
