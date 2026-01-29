import { useEffect, useState } from "react";
import { FeedbackItem, getAllFeedback } from "../api/feedback";

type LoadState = "idle" | "loading" | "loaded" | "error" | "forbidden";

export default function FeedbackViewerPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [state, setState] = useState<LoadState>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setState("loading");
      setError(null);
      try {
        const data = await getAllFeedback();
        if (cancelled) return;
        setItems(data.items);
        setState("loaded");
      } catch (err: any) {
        if (cancelled) return;
        const msg = err?.message || "";
        if (msg.includes("403") || msg.toLowerCase().includes("forbidden")) {
          setState("forbidden");
        } else {
          setState("error");
          setError(msg || "Failed to load feedback");
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === "loading" || state === "idle") {
    return (
      <div style={{ maxWidth: 900, margin: "40px auto" }}>
        <h1>Feedback (admin)</h1>
        <p>Loading feedback...</p>
      </div>
    );
  }

  if (state === "forbidden") {
    return (
      <div style={{ maxWidth: 600, margin: "40px auto" }}>
        <h1>Feedback (admin)</h1>
        <p>You do not have access to this page.</p>
        <p style={{ marginTop: 8 }}>This view is only available for TESKI_ADMIN accounts.</p>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div style={{ maxWidth: 900, margin: "40px auto" }}>
        <h1>Feedback (admin)</h1>
        <p style={{ color: "red" }}>Failed to load feedback.</p>
        {error && <pre style={{ whiteSpace: "pre-wrap" }}>{error}</pre>}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: "40px auto" }}>
      <h1>Feedback (admin)</h1>
      <p style={{ marginBottom: 16 }}>Internal view of feedback submitted by users.</p>
      {items.length === 0 ? (
        <p>No feedback yet.</p>
      ) : (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 14,
          }}
        >
          <thead>
            <tr>
              <th style={thStyle}>Created</th>
              <th style={thStyle}>User</th>
              <th style={thStyle}>Kind</th>
              <th style={thStyle}>Severity</th>
              <th style={thStyle}>Context</th>
              <th style={thStyle}>Message</th>
            </tr>
          </thead>
          <tbody>
            {items.map((fb) => (
              <tr key={fb.id}>
                <td style={tdStyle}>{new Date(fb.created_at).toLocaleString()}</td>
                <td style={tdStyle}>
                  <div className="flex flex-col gap-1">
                    {fb.user_email && <div>{fb.user_email}</div>}
                    {fb.user_id && (
                      <div>
                        <code>{fb.user_id}</code>
                      </div>
                    )}
                  </div>
                </td>
                <td style={tdStyle}>{fb.kind}</td>
                <td style={tdStyle}>{fb.severity || "-"}</td>
                <td style={tdStyle}>
                  <div>
                    {fb.page_url && (
                      <div>
                        <strong>Page:</strong> {fb.page_url}
                      </div>
                    )}
                    {fb.user_agent && (
                      <div className="text-xs text-gray-500">
                        <strong>UA:</strong> {fb.user_agent}
                      </div>
                    )}
                  </div>
                </td>
                <td style={{ ...tdStyle, maxWidth: 420 }}>
                  <div style={{ whiteSpace: "pre-wrap" }}>{fb.message}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  borderBottom: "1px solid #ccc",
  textAlign: "left",
  padding: "8px",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  verticalAlign: "top",
  padding: "8px",
};
