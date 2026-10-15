import type { Archetype } from "../AuditTable";

export const archetypeBadge: Record<Archetype, string> = {
  "Operative Genius": "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 backdrop-blur",
  "Product Purist":   "bg-violet-500/10 text-violet-300 border border-violet-500/20 backdrop-blur",
  "Growth Hacker":    "bg-amber-500/10 text-amber-300 border border-amber-500/20 backdrop-blur",
};

interface Props {
  archetype: Archetype;
}

export default function ArchetypeBadge({ archetype }: Props) {
  return (
    <span
      className={`inline-block text-label uppercase tracking-widest px-2 py-0.5 rounded-sm font-mono ${archetypeBadge[archetype]}`}
    >
      {archetype}
    </span>
  );
}
