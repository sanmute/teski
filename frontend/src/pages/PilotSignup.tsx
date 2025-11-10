import React, { useState } from "react";

function ConsentScreen({ userId }: { userId: string }) {
  async function accept() {
    await fetch("/pilot/consent/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, text_version: "v1" }),
    });
    window.location.href = "/app";
  }

  return (
    <div className="space-y-3">
      <h2 className="font-medium">Consent</h2>
      <div className="rounded bg-gray-50 p-3 text-sm">
        We collect usage (sessions, answers, feedback) to improve Teski. Pilot data is isolated,
        deleted on request, and never shared externally.
      </div>
      <button
        type="button"
        onClick={accept}
        className="w-full rounded bg-black px-3 py-2 text-white"
      >
        I agree and join
      </button>
    </div>
  );
}

export default function PilotSignup() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [userId, setUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setError(null);
    setLoading(true);
    const response = await fetch("/pilot/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    });
    setLoading(false);
    if (!response.ok) {
      const detail = (await response.json()).detail || "Signup failed";
      setError(detail);
      return;
    }
    const payload = await response.json();
    setUserId(payload.user_id);
  }

  return (
    <div className="mx-auto max-w-md space-y-4 p-6">
      <h1 className="text-xl font-semibold">Teski Pilot — Invite Signup</h1>
      {!userId ? (
        <>
          <input
            className="w-full rounded border p-2"
            placeholder="Your email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <input
            className="w-full rounded border p-2"
            placeholder="Invite code"
            value={code}
            onChange={(event) => setCode(event.target.value)}
          />
          <button
            type="button"
            onClick={submit}
            disabled={loading}
            className="w-full rounded bg-black px-3 py-2 text-white disabled:opacity-60"
          >
            {loading ? "Submitting…" : "Continue"}
          </button>
          {error && <div className="text-sm text-red-600">{error}</div>}
        </>
      ) : (
        <ConsentScreen userId={userId} />
      )}
    </div>
  );
}
