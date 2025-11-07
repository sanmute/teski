import React, { useEffect, useState } from "react";
import { API_BASE } from "@/api";

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

  if (!enabled) {
    return (
      <div className="rounded-xl border bg-card p-4 text-sm text-muted-foreground">
        Concept maps are off. Enable them in Settings.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border bg-card p-4 shadow">
      <h3 className="font-semibold">Concept map</h3>
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
    </div>
  );
}
