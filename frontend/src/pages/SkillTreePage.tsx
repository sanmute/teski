import { SkillTreeView } from "@/components/skill-tree/SkillTreeView";

export default function SkillTreePage() {
  return (
    <div className="mx-auto w-full max-w-5xl pb-16">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-slate-900">Skill Map</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track your mastery across foundational, core, and advanced skills. Click any skill to jump
          into a targeted micro-quest.
        </p>
      </div>
      <SkillTreeView />
    </div>
  );
}
