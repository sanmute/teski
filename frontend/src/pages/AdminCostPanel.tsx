import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface CostStats {
  cost_total_eur: number;
  cost_last_30d_eur: number;
  events_total: number;
  cache_hit_rate: number;
}

interface CacheStats {
  total_cached: number;
  cached_last_30d: number;
}

interface Kpis {
  dau: number;
  wau: number;
  retention7_pct: number;
  retention28_pct: number;
  avg_session_minutes: number;
  reviews_per_user_7d: number;
  paid_users: number;
  window_7d_start: string;
  today: string;
}

export default function AdminCostPanel() {
  const [cost, setCost] = useState<CostStats | null>(null);
  const [cache, setCache] = useState<CacheStats | null>(null);
  const [kpis, setKpis] = useState<Kpis | null>(null);

  useEffect(() => {
    fetch("/feedback/admin/stats/costs").then((r) => r.json()).then(setCost).catch(() => undefined);
    fetch("/feedback/admin/stats/cache").then((r) => r.json()).then(setCache).catch(() => undefined);
    fetch("/analytics/admin/kpis").then((r) => r.json()).then(setKpis).catch(() => undefined);
  }, []);

  const chartData = [
    { name: "Cost 30d", value: cost?.cost_last_30d_eur ?? 0 },
    { name: "Total Cost", value: cost?.cost_total_eur ?? 0 },
  ];

  const cacheData = [
    { name: "Cached total", value: cache?.total_cached ?? 0 },
    { name: "Cached 30d", value: cache?.cached_last_30d ?? 0 },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Admin — Costs & KPIs</h1>
          <p className="text-sm text-muted-foreground">Monitor LLM usage, cache performance, and user health.</p>
        </div>
        <Link to="/" className="text-sm font-medium text-primary underline-offset-2 hover:underline">
          ← Back to dashboard
        </Link>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Cost (last 30d)" value={`€${(cost?.cost_last_30d_eur ?? 0).toFixed(2)}`} />
        <Stat label="Total Cost" value={`€${(cost?.cost_total_eur ?? 0).toFixed(2)}`} />
        <Stat label="Events total" value={(cost?.events_total ?? 0).toString()} />
        <Stat label="Cache hit rate" value={`${Math.round((cost?.cache_hit_rate ?? 0) * 100)}%`} />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stat label="DAU (today)" value={(kpis?.dau ?? 0).toString()} />
        <Stat label="WAU (7d)" value={(kpis?.wau ?? 0).toString()} />
        <Stat label="Retention 7d" value={`${kpis?.retention7_pct ?? 0}%`} />
        <Stat label="Retention 28d" value={`${kpis?.retention28_pct ?? 0}%`} />
        <Stat label="Avg session (min)" value={(kpis?.avg_session_minutes ?? 0).toString()} />
        <Stat label="Reviews/user (7d)" value={(kpis?.reviews_per_user_7d ?? 0).toString()} />
        <Stat label="Paid users" value={(kpis?.paid_users ?? 0).toString()} />
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <Card title="Costs">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Cache Stats">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={cacheData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </section>

      <EnvHints />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-muted/40 p-4">
      <div className="text-xs opacity-70">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function Card({ title, children }: React.PropsWithChildren<{ title: string }>) {
  return (
    <div className="rounded-xl border bg-card p-4 shadow">
      <h3 className="mb-3 font-semibold">{title}</h3>
      {children}
    </div>
  );
}

function EnvHints() {
  return (
    <div className="text-xs opacity-70">
      <p>
        <strong>Env:</strong> FEEDBACK_MONTHLY_CAP_EUR, FEEDBACK_CAP_MODE ("mini-only" | "block")
      </p>
    </div>
  );
}
