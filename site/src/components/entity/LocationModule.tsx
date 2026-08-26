import * as React from "react";

import { VoidWell } from "@/components/kit/VoidWell";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { cn } from "@/lib/utils";

/*
 * Entity-page location module (map-viewer §7 M4): the mini schematic
 * placeholder (VoidWell until artwork), the "found in" scene links, and the
 * `/map?focus=<kind>:<id>&scene=<container>` anchor — ALL as plain <a href>
 * in SSR HTML (AC MV-4; the JS-only-link ban is what kills the v0
 * asymmetry). Provenance carry law (F-7): mechanism/status surface whenever
 * mechanism !== "hard" OR status !== "modeled" — same vocabulary and
 * treatment as the PinPopover provenance cell.
 */

export interface LocationSceneRef {
  sceneId: string;
  /** Filler-chain scene title resolved for THIS locale (server-side). */
  sceneTitle: string;
  /** Locale-prefixed /map?focus=… deep link (null → no anchor rendered). */
  focusHref: string | null;
  /** Edge provenance, verbatim from the source relink/marker row. */
  mechanism?: string;
  status?: string;
  /** Container census when the edge hosts >1 instance (never 1-of-N). */
  census?: Record<string, number>;
}

export function LocationModule({
  scenes,
  localePrefix,
  openMapLabel,
  unplacedLabel,
  className,
}: {
  scenes: LocationSceneRef[];
  /** Locale URL prefix (pivot bare, everyone else /code). */
  localePrefix: string;
  /** Localized label of the map deep-link anchor (chrome map.openMap). */
  openMapLabel: string;
  /** Localized aria label for the unplaced well (chrome map.unplaced). */
  unplacedLabel?: string;
  className?: string;
}) {
  // An entity the corpus places nowhere renders an honest unplaced well of
  // equal height to a placed module — no absence sentence (§8 stub policy).
  if (scenes.length === 0) {
    return (
      <VoidWell
        aria-label={unplacedLabel}
        className={cn("aspect-[16/7] w-full", className)}
      />
    );
  }

  return (
    <div data-slot="location-module" className={cn("flex flex-col gap-3", className)}>
      {/* mini schematic placeholder — authored art consumes this slot later */}
      <VoidWell className="aspect-[16/7] w-full" />

      <ul className="flex flex-col gap-1.5">
        {scenes.map((s) => {
          const provenanceBites =
            (Boolean(s.mechanism) && s.mechanism !== "hard") ||
            (Boolean(s.status) && s.status !== "modeled");
          return (
            <li
              key={`${s.sceneId}:${s.focusHref ?? ""}`}
              className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1"
            >
              {/* found in → /locations/<scene_id> */}
              <a
                href={`${localePrefix}/locations/${encodeURIComponent(s.sceneId)}`}
                className="rounded-full px-1 py-0.5 text-sm font-bold hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {s.sceneTitle}
              </a>
              {/* two-way link → scene-locked viewer with this entity focused */}
              {s.focusHref && (
                <a
                  href={s.focusHref}
                  className="inline-flex min-h-11 items-center rounded-full bg-secondary px-3 font-lcd text-xs uppercase tracking-wide text-secondary-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {openMapLabel}
                </a>
              )}
              {provenanceBites && (
                <LcdTerminal className="w-fit rounded-full px-2.5 py-0.5 text-xs">
                  {[s.mechanism, s.status].filter(Boolean).join(" · ")}
                </LcdTerminal>
              )}
              {s.census &&
                Object.entries(s.census).map(([k, v]) => (
                  <span
                    key={k}
                    className="rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-[var(--ms-signal)]"
                  >
                    {k}:{v}
                  </span>
                ))}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
