import React, { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/api";

type Overview = {
  users_total: number;
  sessions_total: number;
  consents: number;
  depth_avg: number;
  costs: {
    cost_total_eur: number;
    cost_last_30d_eur: number;
    events_total: number;
    cache_hit_rate: number;
  };
};

export default function PilotAdmin() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [depth, setDepth] = useState<any[]>([]);
  const [csv, setCsv] = useState<string>("");

  const authHeader = useMemo(() => {
    if (typeof window === "undefined") return "";
    return "Basic " + window.btoa("teski:pilot");
  }, []);

  useEffect(() => {
    if (!authHeader) return;
    const headers = { Authorization: authHeader };
    apiFetch<Overview>("/pilot/admin/overview", { headers })
      .then(setOverview)
      .catch(() => setOverview(null));
    apiFetch<any[]>("/pilot/admin/users", { headers })
      .then(setUsers)
      .catch(() => setUsers([]));
    apiFetch<any[]>("/pilot/admin/sessions?limit=100", { headers })
      .then(setSessions)
      .catch(() => setSessions([]));
    apiFetch<any[]>("/pilot/admin/depth?limit=100", { headers })
      .then(setDepth)
      .catch(() => setDepth([]));
  }, [authHeader]);

  async function loadReport() {
    if (!authHeader) return;
    const payload = await apiFetch<{ csv?: string }>("/pilot/admin/report", {
      headers: { Authorization: authHeader },
    }).catch(() => null);
    if (!payload) return;
    setCsv(payload.csv || "");
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Pilot Admin</h1>

      {overview && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Users" value={overview.users_total} />
          <Stat label="Consents" value={overview.consents} />
          <Stat label="Sessions" value={overview.sessions_total} />
          <Stat label="Avg Depth" value={overview.depth_avg.toFixed(1)} />
          <Stat label="Cost 30d (€)" value={overview.costs.cost_last_30d_eur.toFixed(2)} />
          <Stat label="Total Cost (€)" value={overview.costs.cost_total_eur.toFixed(2)} />
          <Stat label="Events" value={overview.costs.events_total} />
          <Stat
            label="Cache Hit"
            value={`${Math.round((overview.costs.cache_hit_rate || 0) * 100)}%`}
          />
        </div>
      )}

      <section>
        <h3 className="mb-2 font-semibold">Recent Sessions</h3>
        <div className="overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead>
              <tr>
                <Th>ID</Th>
                <Th>User</Th>
                <Th>Topic</Th>
                <Th>Minutes</Th>
                <Th>Start</Th>
                <Th>End</Th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((row) => (
                <tr key={row.id}>
                  <Td>{row.id}</Td>
                  <Td>{row.user_id}</Td>
                  <Td>{row.topic_id || "—"}</Td>
                  <Td>{row.minutes_active}</Td>
                  <Td>{row.started_at}</Td>
                  <Td>{row.ended_at || ""}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Depth Samples</h3>
        <div className="overflow-auto rounded border">
          <table className="min-w-full text-sm">
            <thead>
              <tr>
                <Th>User</Th>
                <Th>Topic</Th>
                <Th>Score</Th>
                <Th>At</Th>
              </tr>
            </thead>
            <tbody>
              {depth.map((row) => (
                <tr key={`${row.user_id}-${row.created_at}`}>
                  <Td>{row.user_id}</Td>
                  <Td>{row.topic_id}</Td>
                  <Td>{row.score}</Td>
                  <Td>{row.created_at}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="flex items-center gap-3">
        <button
          type="button"
          onClick={loadReport}
          className="rounded bg-black px-3 py-2 text-white"
        >
          Generate Report
        </button>
        {csv && (
          <a
            href={`data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`}
            download="teski_pilot_report.csv"
            className="rounded bg-gray-200 px-3 py-2"
          >
            Download CSV
          </a>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="border-b px-3 py-2 text-left">{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="border-b px-3 py-2">{children}</td>;
}
