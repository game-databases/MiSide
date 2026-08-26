"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import { VoidWell } from "@/components/kit/VoidWell";
import { projectedCoordinates } from "./projection";
import { formatFocus, parseFocus } from "./mapState";

/*
 * SceneMap — the Leaflet island (spec §7). Imagery: AUTHORED schematics;
 * artwork is a separate piece, so v0 renders the module + registry with an
 * honest schematic grid — no third-party embeds anywhere (negative-grep
 * launch gate).
 *
 * Markers consume the scenes dataset, never raw dumps: ONLY markers.jsonl
 * rows may render; that file is _meta-only in v0 (no-orphan rule), so the
 * module MUST render zero markers honestly until the projection rerun lands
 * them. Coordinates pass through projectedCoordinates() — the same function
 * the server uses; a non-projecting cell never plots.
 *
 * Focus state rides the URL: ?focus=<entity_kind>:<entity_slug>&scene=… —
 * restored on load, updated via replaceState (never navigation keystrokes).
 */

export interface MapMarkerInput {
  entity_kind: string;
  entity_slug: string;
  scene_id: string;
  source: "inline" | "pptr-unresolved" | "none";
  space?: string;
  x?: number;
  y?: number;
}

export interface SceneRegistryEntry {
  scene_id: string;
  role: string;
  bounds: [number, number, number, number] | null;
  zoom: [number, number];
  "coordinate-transform": "rect-per-map";
  imagery: "authored";
  status: "awaiting-artwork" | "ready";
}

export function SceneMap({
  registry,
  rows,
  pendingLabel,
  localePrefix,
  className,
}: {
  registry: SceneRegistryEntry[];
  /** markers.jsonl rows only (zero today). */
  rows: MapMarkerInput[];
  pendingLabel: string;
  localePrefix: string;
  className?: string;
}) {
  const hostRef = React.useRef<HTMLDivElement | null>(null);
  const [focus, setFocus] = React.useState<{ kind: string; slug: string } | null>(
    null
  );

  // Restore focus state from the URL on first client render.
  React.useEffect(() => {
    const parsed = parseFocus(new URLSearchParams(window.location.search));
    if (parsed) setFocus({ kind: parsed.kind, slug: parsed.slug });
  }, []);

  const updateFocus = React.useCallback(
    (next: { kind: string; slug: string } | null) => {
      setFocus(next);
      const url = new URL(window.location.href);
      if (next) {
        const q = formatFocus({ kind: next.kind, slug: next.slug }).slice(1);
        for (const [k] of url.searchParams) {
          if (k === "focus" || k === "scene") url.searchParams.delete(k);
        }
        for (const [k, v] of new URLSearchParams(q)) url.searchParams.set(k, v);
      } else {
        url.searchParams.delete("focus");
        url.searchParams.delete("scene");
      }
      // replaceState, never navigation — map state is a URL without keystrokes
      window.history.replaceState(null, "", url);
    },
    []
  );

  // Leaflet island: dynamic import keeps it out of every other route's bundle.
  const mapRef = React.useRef<{ remove: () => void } | null>(null);
  React.useEffect(() => {
    let disposed = false;
    void (async () => {
      const L = await import("leaflet");
      if (disposed || !hostRef.current || mapRef.current) return;
      // leaflet's base styles ship via globals.css @import
      const entry = registry[0];
      const map = L.map(hostRef.current, {
        crs: L.CRS.Simple,
        minZoom: entry?.zoom?.[0] ?? 1,
        maxZoom: entry?.zoom?.[1] ?? 4,
        attributionControl: false,
      });
      map.setView([0, 0], Math.min(2, entry?.zoom?.[1] ?? 4));
      mapRef.current = map;
      // Authored schematics land in public/map/<scene_id>/ as the artwork
      // piece delivers them; until then the schematic grid IS the honest state.
    })();
    return () => {
      disposed = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [registry]);

  // The conjunction gate runs HERE, browser-side, through the shared function.
  const projected = rows
    .map((r) => ({ row: r, coords: projectedCoordinates(r) }))
    .filter((m) => m.coords !== null) as Array<{
    row: MapMarkerInput;
    coords: { x: number; y: number };
  }>;

  return (
    <div data-slot="scene-map" className={cn("flex flex-col gap-3", className)}>
      <div
        ref={hostRef}
        className="relative h-80 w-full overflow-hidden rounded-lg border border-border"
      >
        {/* schematic grid — authored artwork replaces this when it lands */}
        <div
          aria-hidden
          className="absolute inset-0 [background-image:repeating-linear-gradient(0deg,color-mix(in_srgb,var(--ms-bg-2)_38%,transparent)_0_1px,transparent_1px_32px),repeating-linear-gradient(90deg,color-mix(in_srgb,var(--ms-bg-2)_38%,transparent)_0_1px,transparent_1px_32px)]"
        />
        {projected.length === 0 && (
          <VoidWell className="absolute inset-3 rounded-md border-dashed opacity-70" aria-label={pendingLabel} />
        )}
        {focus && (
          <button
            type="button"
            onClick={() => updateFocus(null)}
            className="absolute end-3 top-3 rounded-full bg-secondary px-3 py-1 font-lcd text-xs text-secondary-foreground"
          >
            focus: {focus.kind}:{focus.slug}
          </button>
        )}
      </div>
      {/* two-way links: marker → entity pages stay crawlable anchors */}
      {projected.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {projected.map((m) => (
            <li key={`${m.row.entity_kind}:${m.row.entity_slug}`}>
              <a
                href={`${localePrefix}/${m.row.entity_kind}/${m.row.entity_slug}`}
                className="inline-block rounded-full bg-secondary px-2.5 py-0.5 font-lcd text-xs hover:bg-accent"
              >
                {m.row.entity_slug}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
