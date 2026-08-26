/*
 * Position truth is a source×space CONJUNCTION, not source alone (spec §7).
 * Dispositions are TOTAL over the axis; the projection binds to
 * `source=="inline" AND space=="world-assumed"` and NO other cell.
 * Unit-tested over the full axis table (AC S7).
 *
 * | source          | space               | disposition      |
 * |-----------------|---------------------|------------------|
 * | inline          | world-assumed       | PROJECTED        |
 * | inline          | unknown             | pending-placement|
 * | inline          | parent-local        | pending-placement|
 * | inline          | object-local-offset | pending-placement|
 * | pptr-unresolved | any                 | pending-placement|
 * | none            | —                   | pending-placement|
 */

export type SourceClass = "inline" | "pptr-unresolved" | "none";

export interface PlacementInput {
  source: SourceClass;
  space?: string;
  x?: number;
  y?: number;
  z?: number;
}

export interface PlacementDecision {
  disposition: "PROJECTED" | "PENDING";
  /** Axis cell label for telemetry/ledger surfaces. */
  cell: string;
}

export function placementDecision(p: PlacementInput): PlacementDecision {
  if (p.source === "inline" && p.space === "world-assumed") {
    return { disposition: "PROJECTED", cell: "inline/world-assumed" };
  }
  const space = p.space ?? "—";
  return { disposition: "PENDING", cell: `${p.source}/${space}` };
}

/**
 * The ONLY path from a placement row to map coordinates. Returns null for
 * every non-projecting cell — including the inline-but-space:unknown
 * Player_Teleport class and every parent-local / object-local-offset row.
 * Same function on server and browser (searchRows law applied to maps).
 */
export function projectedCoordinates(
  p: PlacementInput
): { x: number; y: number; z?: number } | null {
  const d = placementDecision(p);
  if (d.disposition !== "PROJECTED") return null;
  if (typeof p.x !== "number" || typeof p.y !== "number") return null;
  return { x: p.x, y: p.y, z: p.z };
}

/*
 * Marker-row v2 bridge (map-viewer §4.2). A marker plots iff its emitted
 * `status:"projected"` AGREES with the conjunction above — the same gate,
 * never a second one.
 */

export interface MarkerPositionInput {
  status: string;
  x?: number | null;
  y?: number | null;
  z?: number | null;
}

/** Coordinates for a marker row — null unless projected AND projecting. */
export function markerCoordinates(
  m: MarkerPositionInput
): { x: number; y: number; z?: number } | null {
  if (m.status !== "projected") return null;
  return projectedCoordinates({
    source: "inline",
    space: "world-assumed",
    x: m.x ?? undefined,
    y: m.y ?? undefined,
    z: m.z ?? undefined,
  });
}

/**
 * AC MV-2 agreement check: true when the emitted status and the projection
 * conjunction DISAGREE in either direction (fixture-test hook).
 */
export function markerStatusDisagrees(m: MarkerPositionInput): boolean {
  const coords = projectedCoordinates({
    source: "inline",
    space: "world-assumed",
    x: m.x ?? undefined,
    y: m.y ?? undefined,
    z: m.z ?? undefined,
  });
  const claimsProjected = m.status === "projected";
  return claimsProjected !== (coords !== null);
}
