import React, { ReactNode, useEffect, useRef, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from "recharts";
import * as htmlToImage from "html-to-image";
import jsPDF from "jspdf";
import { apiFetch } from "@/api";

type KPI = {
  range_days: number;
  dau: { date: string; dau: number }[];
  avg_depth: { date: string; avg_depth: number }[];
  minutes: { date: string; minutes: number }[];
  cohorts: { cohort: string; W0: number; W1: number; W2: number; W3: number; W4: number }[];
  depth_hist: { bucket: string; count: number }[];
  costs: {
    total_eur: number;
    last_30d_eur: number;
    events_total: number;
    cache_hit_rate: number;
    cost_per_active_user_30d: number;
  };
};

const palette = ["#2563eb", "#16a34a", "#f97316", "#a855f7", "#0ea5e9"];

export default function InvestorDashboard() {
  const [data, setData] = useState<KPI | null>(null);
  const [range, setRange] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const boardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setError(null);
      try {
        const payload = await apiFetch<KPI>(`/analytics/investor?range_days=${range}`);
        if (!cancelled) {
          setData(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load dashboard data.");
          setData(null);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [range]);

  async function exportPNG() {
    if (!boardRef.current) return;
    const url = await htmlToImage.toPng(boardRef.current);
    const a = document.createElement("a");
    a.href = url;
    a.download = `teski-investor-${range}d.png`;
    a.click();
  }

  async function exportPDF() {
    if (!boardRef.current) return;
    const url = await htmlToImage.toPng(boardRef.current, { pixelRatio: 2 });
    const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: "a4" });
    const img = new Image();
    img.src = url;
    await new Promise<void>((resolve) => {
      img.onload = () => resolve();
    });
    const pageWidth = pdf.internal.pageSize.getWidth();
    const margin = 20;
    const scale = (pageWidth - margin * 2) / img.width;
    pdf.addImage(img, "PNG", margin, margin, img.width * scale, img.height * scale);
    pdf.save(`teski-investor-${range}d.pdf`);
  }

  if (error) {
    return (
      <div className="p-6 space-y-4">
        <Header
          range={range}
          onRangeChange={setRange}
          onExportPNG={exportPNG}
          onExportPDF={exportPDF}
        />
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <Header
          range={range}
          onRangeChange={setRange}
          onExportPNG={exportPNG}
          onExportPDF={exportPDF}
        />
        <div className="mt-6 rounded-xl border bg-white p-6">Loading…</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <Header
        range={range}
        onRangeChange={setRange}
        onExportPNG={exportPNG}
        onExportPDF={exportPDF}
      />

      <div ref={boardRef} className="space-y-6 rounded-2xl bg-white p-6 shadow-xl">
        <KPICards data={data} />

        <Section title="Daily Active Users (DAU)">
          <LineBlock data={data.dau} x="date" lines={[{ k: "dau", label: "DAU" }]} />
        </Section>

        <Section title="Average Depth Score">
          <LineBlock data={data.avg_depth} x="date" lines={[{ k: "avg_depth", label: "Avg Depth" }]} />
        </Section>

        <Section title="Total Minutes Active">
          <LineBlock data={data.minutes} x="date" lines={[{ k: "minutes", label: "Minutes" }]} />
        </Section>

        <Section title="Depth Score Distribution">
          <BarBlock data={data.depth_hist} x="bucket" bars={[{ k: "count", label: "Count" }]} />
        </Section>

        <Section title="Cohort Retention (W0–W4)">
          <CohortTable cohorts={data.cohorts} />
        </Section>
      </div>
    </div>
  );
}

function Header({
  range,
  onRangeChange,
  onExportPNG,
  onExportPDF,
}: {
  range: number;
  onRangeChange: (value: number) => void;
  onExportPNG: () => void;
  onExportPDF: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-semibold">Investor Dashboard</h1>
      <div className="flex flex-wrap items-center gap-2">
        <select
          className="rounded border px-2 py-1 text-sm"
          value={range}
          onChange={(event) => onRangeChange(parseInt(event.target.value, 10))}
        >
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
        </select>
        <button
          type="button"
          onClick={onExportPNG}
          className="rounded-lg bg-black px-3 py-2 text-sm font-medium text-white"
        >
          Export PNG
        </button>
        <button
          type="button"
          onClick={onExportPDF}
          className="rounded-lg bg-gray-100 px-3 py-2 text-sm font-medium text-gray-900"
        >
          Export PDF
        </button>
      </div>
    </div>
  );
}

function KPICards({ data }: { data: KPI }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
      <Card label="Cost (30d €)" value={data.costs.last_30d_eur.toFixed(2)} />
      <Card label="Total Cost (€)" value={data.costs.total_eur.toFixed(2)} />
      <Card label="Events" value={data.costs.events_total.toLocaleString()} />
      <Card label="Cache Hit" value={`${Math.round((data.costs.cache_hit_rate || 0) * 100)}%`} />
      <Card
        label="Cost / Active (30d)"
        value={data.costs.cost_per_active_user_30d.toFixed(3)}
      />
    </div>
  );
}

function Card({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-2xl border bg-gray-50 p-4">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
      <div className="h-64 rounded-2xl border bg-white p-3">{children}</div>
    </section>
  );
}

function LineBlock({
  data,
  x,
  lines,
}: {
  data: any[];
  x: string;
  lines: { k: string; label: string; color?: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={x} />
        <YAxis />
        <Tooltip />
        {lines.map((line, idx) => (
          <Line
            key={line.k}
            type="monotone"
            dataKey={line.k}
            name={line.label}
            dot={false}
            stroke={line.color || palette[idx % palette.length]}
            strokeWidth={2}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function BarBlock({
  data,
  x,
  bars,
}: {
  data: any[];
  x: string;
  bars: { k: string; label: string; color?: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={x} />
        <YAxis />
        <Tooltip />
        <Legend />
        {bars.map((bar, idx) => (
          <Bar
            key={bar.k}
            dataKey={bar.k}
            name={bar.label}
            fill={bar.color || palette[idx % palette.length]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function CohortTable({ cohorts }: { cohorts: KPI["cohorts"] }) {
  if (!cohorts.length) {
    return (
      <div className="rounded-xl border bg-gray-50 p-4 text-sm text-gray-500">
        No pilot cohorts yet.
      </div>
    );
  }
  return (
    <div className="overflow-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <Th>Cohort (Signup Week)</Th>
            <Th>W0</Th>
            <Th>W1</Th>
            <Th>W2</Th>
            <Th>W3</Th>
            <Th>W4</Th>
          </tr>
        </thead>
        <tbody>
          {cohorts.map((cohort) => (
            <tr key={cohort.cohort}>
              <Td>{cohort.cohort}</Td>
              <Td>{cohort.W0}%</Td>
              <Td>{cohort.W1}%</Td>
              <Td>{cohort.W2}%</Td>
              <Td>{cohort.W3}%</Td>
              <Td>{cohort.W4}%</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: ReactNode }) {
  return <th className="border-b bg-gray-50 px-3 py-2 text-left">{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td className="border-b px-3 py-2">{children}</td>;
}
