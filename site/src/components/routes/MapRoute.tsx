import { SceneMap } from "@/components/map/SceneMap";
import { markers, scenes } from "@/data/contracts";
import type { Chrome } from "@/i18n/request";

/*
 * /map — SSG shell + Leaflet island (spec §7). Registry from scenes.jsonl
 * (24 rows, rect-per-map assumed until P5/S9 calibration); markers consume
 * ONLY markers.jsonl rows — zero today (no-orphan rule), rendered honestly.
 */
export function MapRoute({
  chrome,
  localePrefix,
}: {
  chrome: Chrome;
  localePrefix: string;
}) {
  const registry = scenes().map((s) => ({
    scene_id: s.scene_id,
    role: s.role,
    // bounds settle at the calibration rerun; null is the honest value
    bounds: null,
    zoom: [1, 4] as [number, number],
    "coordinate-transform": "rect-per-map" as const,
    imagery: "authored" as const,
    status: "awaiting-artwork" as const,
  }));
  // markers.jsonl rows only; v0 = _meta-only → zero markers render
  const rows = markers().map((m) => ({
    entity_kind: String((m as Record<string, unknown>).entity_kind ?? ""),
    entity_slug: String((m as Record<string, unknown>).entity_slug ?? ""),
    scene_id: String((m as Record<string, unknown>).scene_id ?? ""),
    source: "inline" as const,
  }));
  return (
    <SceneMap
      registry={registry}
      rows={rows}
      pendingLabel={chrome["map.pendingPlacement"]}
      localePrefix={localePrefix}
    />
  );
}
