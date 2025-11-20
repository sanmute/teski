import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listUserMastery, type SkillMastery } from "@/api";
import { getClientUserId } from "@/lib/user";
import { SKILL_DEFINITIONS, type SkillDefinition } from "@/data/skillTree";
import type { SkillNodeView, SkillStatus } from "./SkillNodeCard";
import { SkillNodeCard } from "./SkillNodeCard";
import { SkillDetailPanel } from "./SkillDetailPanel";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

const computeDepth = (definition: SkillDefinition, lookup: Record<string, SkillDefinition>, memo: Record<string, number>): number => {
  if (memo[definition.id] !== undefined) return memo[definition.id];
  if (definition.prerequisites.length === 0) {
    memo[definition.id] = 0;
    return 0;
  }
  const depth =
    1 +
    Math.max(
      0,
      ...definition.prerequisites.map((pid) => {
        const prereq = lookup[pid];
        if (!prereq) return 0;
        return computeDepth(prereq, lookup, memo);
      }),
    );
  memo[definition.id] = depth;
  return depth;
};

const getStatus = (mastery: number, prereqMasteries: number[]): SkillStatus => {
  if (mastery >= 70) return "strong";
  const prereqWeak = prereqMasteries.some((value) => value < 30);
  if (mastery < 20 || prereqWeak) return "locked";
  return "in_progress";
};

export function SkillTreeView() {
  const userId = useMemo(() => getClientUserId(), []);
  const navigate = useNavigate();
  const [mastery, setMastery] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SkillNodeView | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      try {
        const data = await listUserMastery(userId);
        if (!mounted) return;
        const map: Record<string, number> = {};
        data.forEach((item) => {
          map[item.skill_id] = item.mastery;
        });
        setMastery(map);
        setError(null);
      } catch (err) {
        console.error(err);
        if (mounted) setError("Could not load mastery data.");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [userId]);

  const nodes = useMemo(() => {
    const byId = Object.fromEntries(SKILL_DEFINITIONS.map((def) => [def.id, def]));
    const depthMemo: Record<string, number> = {};
    const childMap: Record<string, string[]> = {};
    SKILL_DEFINITIONS.forEach((def) => {
      def.prerequisites.forEach((pid) => {
        if (!childMap[pid]) childMap[pid] = [];
        childMap[pid].push(def.id);
      });
    });

    return SKILL_DEFINITIONS.map<SkillNodeView>((def) => {
      const depth = computeDepth(def, byId, depthMemo);
      const masteryValue = mastery[def.id] ?? 0;
      const prereqMasteries = def.prerequisites.map((pid) => mastery[pid] ?? 0);
      const status = getStatus(masteryValue, prereqMasteries);
      const recommended =
        status !== "strong" &&
        (def.prerequisites.length === 0 || def.prerequisites.every((pid) => (mastery[pid] ?? 0) >= 40));
      return {
        id: def.id,
        name: def.name,
        description: def.description,
        category: def.category,
        mastery: masteryValue,
        status,
        depth,
        prerequisites: def.prerequisites,
        children: childMap[def.id] ?? [],
        recommended,
      };
    });
  }, [mastery]);

  const tiers = useMemo(() => {
    const grouped: Record<number, SkillNodeView[]> = {};
    nodes.forEach((node) => {
      if (!grouped[node.depth]) grouped[node.depth] = [];
      grouped[node.depth].push(node);
    });
    return Object.keys(grouped)
      .map((depth) => ({
        depth: Number(depth),
        nodes: grouped[Number(depth)].sort((a, b) => a.name.localeCompare(b.name)),
      }))
      .sort((a, b) => a.depth - b.depth);
  }, [nodes]);

  const recommended = useMemo(() => nodes.filter((node) => node.recommended && node.status !== "strong").slice(0, 3), [nodes]);

  const handleSelect = (node: SkillNodeView) => {
    setSelected(node);
    setDetailOpen(true);
  };

  const handleStart = (node: SkillNodeView) => {
    setDetailOpen(false);
    navigate(`/micro-quest?skill_id=${node.id}&len=5`);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-5 w-56" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {error}
        <div className="mt-3">
          <Button variant="outline" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {recommended.length > 0 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested focus</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {recommended.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => handleSelect(node)}
                className="rounded-full bg-slate-900/5 px-3 py-1 text-sm font-semibold text-slate-900 transition hover:bg-slate-900/10"
              >
                {node.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
        {tiers.map((tier) => (
          <div key={tier.depth} className="flex-1 space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {tier.nodes[0]?.category ?? `Tier ${tier.depth + 1}`}
              </p>
            </div>
            {tier.nodes.map((node) => (
              <SkillNodeCard key={node.id} node={node} onSelect={handleSelect} />
            ))}
          </div>
        ))}
      </div>

      <SkillDetailPanel open={detailOpen} node={selected} onClose={() => setDetailOpen(false)} onStart={handleStart} />
    </div>
  );
}
