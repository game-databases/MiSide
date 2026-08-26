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
