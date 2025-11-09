import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Node = { id: string; label: string };
type Edge = { from: string; to: string; label?: string };
type Graph = { nodes: Node[]; edges: Edge[] };

export function ConceptMapWidget({
  userId,
  topicId,
  enabled = true,
}: {
  userId: string;
  topicId: string;
  enabled?: boolean;
}) {
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [nodeLabel, setNodeLabel] = useState("");
  const [edgeFrom, setEdgeFrom] = useState("");
  const [edgeTo, setEdgeTo] = useState("");
  const [tab, setTab] = useState<"edit" | "visualize">("edit");

  useEffect(() => {
    if (!enabled) return;
    fetch(`${API_BASE}/deep/conceptmap/me?user_id=${userId}&topic_id=${topicId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.graph_json) setGraph(data.graph_json);
      })
      .catch(() => undefined);
  }, [userId, topicId, enabled]);

  const addNode = () => {
    const trimmed = nodeLabel.trim();
    if (!trimmed) return;
    const id = trimmed.toLowerCase().replace(/\\s+/g, "-");
    if (graph.nodes.find((n) => n.id === id)) return;
    setGraph((prev) => ({ ...prev, nodes: [...prev.nodes, { id, label: trimmed }] }));
    setNodeLabel("");
  };

  const addEdge = () => {
    if (!edgeFrom || !edgeTo) return;
    setGraph((prev) => ({
      ...prev,
      edges: [...prev.edges, { from: edgeFrom, to: edgeTo, label: "relates_to" }],
    }));
    setEdgeFrom("");
    setEdgeTo("");
  };

  const save = async () => {
    if (!enabled) return;
    await fetch(`${API_BASE}/deep/conceptmap/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, topic_id: topicId, graph_json: graph }),
    }).catch(() => undefined);
  };

  const positionedNodes = useMemo(() => {
    if (!graph.nodes.length) return [];
    const size = 360;
    const radius = Math.min(140, size / 2 - 35);
    return graph.nodes.map((node, idx) => {
      const angle = (2 * Math.PI * idx) / graph.nodes.length;
      const cx = size / 2 + radius * Math.cos(angle);
      const cy = size / 2 + radius * Math.sin(angle);
      return { ...node, x: cx, y: cy };
    });
  }, [graph.nodes]);

  const positionedById = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    positionedNodes.forEach((node) => {
      map[node.id] = { x: node.x, y: node.y };
    });
    return map;
  }, [positionedNodes]);

  if (!enabled) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground">
        Concept maps are off. Enable them in Settings.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border bg-card p-4 shadow">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-semibold">Concept map</h3>
        <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)} className="w-auto">
          <TabsList className="grid grid-cols-2">
            <TabsTrigger value="edit">Edit</TabsTrigger>
            <TabsTrigger value="visualize">Visualize</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
        <TabsContent value="edit" className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <input
              className="flex-1 rounded border bg-background px-2 py-1 text-sm"
              placeholder="New node label"
              value={nodeLabel}
              onChange={(e) => setNodeLabel(e.target.value)}
            />
            <button className="rounded bg-muted px-3 py-1 text-sm" onClick={addNode}>
              Add node
            </button>
            <button className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground" onClick={save}>
              Save map
            </button>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            <select
              className="rounded border bg-background px-2 py-1"
              value={edgeFrom}
              onChange={(e) => setEdgeFrom(e.target.value)}
            >
              <option value="">From…</option>
              {graph.nodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.label}
                </option>
              ))}
            </select>
            <select
              className="rounded border bg-background px-2 py-1"
              value={edgeTo}
              onChange={(e) => setEdgeTo(e.target.value)}
            >
              <option value="">To…</option>
              {graph.nodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.label}
                </option>
              ))}
            </select>
            <button className="rounded bg-muted px-3 py-1 text-sm" onClick={addEdge}>
              Add edge
            </button>
          </div>
          <div className="text-xs text-muted-foreground">
            Nodes: {graph.nodes.length} · Edges: {graph.edges.length}
          </div>
        </TabsContent>

        <TabsContent value="visualize" className="space-y-3">
          {graph.nodes.length === 0 ? (
            <div className="rounded-lg border border-dashed bg-muted/30 p-4 text-sm text-muted-foreground">
              Add a few nodes to see the network visualization.
            </div>
          ) : (
            <div className="rounded-2xl border bg-muted/10 p-3">
              <svg viewBox="0 0 360 360" className="h-[320px] w-full">
                <defs>
                  <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <polygon points="0 0, 6 3, 0 6" fill="currentColor" />
                  </marker>
                </defs>
                {graph.edges.map((edge, idx) => {
                  const from = positionedById[edge.from];
                  const to = positionedById[edge.to];
                  if (!from || !to) return null;
                  return (
                    <line
                      key={`${edge.from}-${edge.to}-${idx}`}
                      x1={from.x}
                      y1={from.y}
                      x2={to.x}
                      y2={to.y}
                      stroke="hsl(var(--primary))"
                      strokeWidth={1.5}
                      markerEnd="url(#arrowhead)"
                      strokeOpacity={0.4}
                    />
                  );
                })}
                {positionedNodes.map((node) => (
                  <g key={node.id}>
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={24}
                      fill="hsl(var(--card))"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                    />
                    <text
                      x={node.x}
                      y={node.y}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="hsl(var(--foreground))"
                      fontSize="12"
                    >
                      {node.label}
                    </text>
                  </g>
                ))}
              </svg>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
