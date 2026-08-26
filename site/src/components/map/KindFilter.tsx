"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import { kindChipStyle } from "./kindAxis";

/*
 * KindFilter (map-viewer §5): chip row over the poi-kind vocabulary restricted
 * to kinds present in the active scene's markers, per-kind counts, Show All /
 * Hide All. Hovering a chip highlights its pins and hovering a pin highlights
 * its chip — the bidirectional join of design-standard §5.3; tint-only hover
 * would fail review. Every target ≥44 px (AC MV-7).
 */
export function KindFilter({
  kinds,
  hoveredKind,
  onToggle,
  onHover,
  onShowAll,
  onHideAll,
  showAllLabel,
  hideAllLabel,
}: {
  kinds: Array<{ kind: string; count: number; enabled: boolean }>;
  hoveredKind: string | null;
  onToggle: (kind: string) => void;
  onHover: (kind: string | null) => void;
  onShowAll: () => void;
  onHideAll: () => void;
  showAllLabel: string;
  hideAllLabel: string;
}) {
  if (kinds.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      {kinds.map(({ kind, count, enabled }) => (
        <button
          key={kind}
          type="button"
          aria-pressed={enabled}
          onMouseEnter={() => onHover(kind)}
          onMouseLeave={() => onHover(null)}
          onFocus={() => onHover(kind)}
          onBlur={() => onHover(null)}
          onClick={() => onToggle(kind)}
          style={kindChipStyle(kind, enabled)}
          className={cn(
            "inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-xs font-bold uppercase tracking-wide transition-[filter] hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            hoveredKind === kind && "ring-2 ring-ring",
            !enabled && "opacity-60"
          )}
        >
          <span>{kind}</span>
          <span className="font-lcd text-[var(--ms-signal)]">{count}</span>
        </button>
      ))}
      <button
        type="button"
        onClick={onShowAll}
        className="inline-flex min-h-11 items-center rounded-full bg-secondary px-4 text-xs font-bold uppercase tracking-wide text-secondary-foreground hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {showAllLabel}
      </button>
      <button
        type="button"
        onClick={onHideAll}
        className="inline-flex min-h-11 items-center rounded-full bg-secondary px-4 text-xs font-bold uppercase tracking-wide text-secondary-foreground hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {hideAllLabel}
      </button>
    </div>
  );
}
