"use client";

import * as React from "react";

import type { SwitcherGroup } from "./viewTypes";

/*
 * SceneSwitcher (map-viewer §5): all 24 scenes grouped story-by-chapter
 * pointer order, then boot/title/menu/unbound; labels ride the registry
 * filler chain (localized chapter name → re-spaced id). A native select with
 * optgroups keeps keyboard + RTL + ≥44 px behavior for free. Writes ?scene=
 * via pushState — the one control allowed to grow the back trail (OQ-5).
 */
export function SceneSwitcher({
  groups,
  sceneId,
  label,
  onSelect,
}: {
  groups: SwitcherGroup[];
  sceneId: string;
  /** Accessible name of the control (chrome map.scenes). */
  label: string;
  onSelect: (sceneId: string) => void;
}) {
  return (
    <select
      aria-label={label}
      value={sceneId}
      onChange={(e) => onSelect(e.target.value)}
      className="h-11 min-w-0 max-w-full rounded-full border border-border bg-secondary px-4 text-sm font-bold text-secondary-foreground hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {groups.map((g) => (
        <optgroup key={g.id} label={g.label}>
          {g.scenes.map((s) => (
            <option key={s.scene_id} value={s.scene_id}>
              {s.label}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
