/*
 * AC S7 (unit half): the source×space conjunction gate is TOTAL over the
 * axis table and ONLY inline+world-assumed projects — including the
 * inline-but-space:unknown Player_Teleport class and every parent-local /
 * object-local-offset row. Plus a full sweep of the real poi.jsonl corpus:
 * no non-projecting cell yields coordinates.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  placementDecision,
  projectedCoordinates,
} from "../src/components/map/projection.ts";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const PACK_ROOT = join(SITE_DIR, "..", "..");

test("axis totality: every documented cell has its pinned disposition", () => {
  const cases = [
    [{ source: "inline", space: "world-assumed" }, "PROJECTED"],
    [{ source: "inline", space: "unknown" }, "PENDING"],
    [{ source: "inline", space: "parent-local" }, "PENDING"],
    [{ source: "inline", space: "object-local-offset" }, "PENDING"],
    [{ source: "pptr-unresolved", space: "unknown" }, "PENDING"],
    [{ source: "pptr-unresolved", space: "world-assumed" }, "PENDING"], // conjunction, never source alone
    [{ source: "none", space: undefined }, "PENDING"],
  ];
  for (const [input, expected] of cases) {
    assert.equal(placementDecision(input).disposition, expected, JSON.stringify(input));
  }
});

test("Player_Teleport class: inline floats but NO proven frame → never plots", () => {
  const coords = projectedCoordinates({
    source: "inline",
    space: "unknown",
    x: -6.172363,
    y: 1.25,
    z: 3.5,
  });
  assert.equal(coords, null);
});

test("projectedCoordinates returns numbers ONLY for the projecting cell", () => {
  const ok = projectedCoordinates({
    source: "inline",
    space: "world-assumed",
    x: -6.172363,
    y: 0,
    z: 9,
  });
  assert.deepEqual(ok, { x: -6.172363, y: 0, z: 9 });
  for (const bad of [
    { source: "inline", space: "parent-local", x: 1, y: 2 },
    { source: "inline", space: "object-local-offset", x: 1, y: 2 },
    { source: "pptr-unresolved", space: "world-assumed", x: 1, y: 2 },
    { source: "none" },
    { source: "inline", space: "weird-future-value", x: 1, y: 2 }, // fail-safe default
  ]) {
    assert.equal(projectedCoordinates(bad), null, JSON.stringify(bad));
  }
});

test("full poi.jsonl sweep: zero non-projecting rows produce coordinates", () => {
  const lines = readFileSync(
    join(PACK_ROOT, "extracted/data/scenes/poi.jsonl"),
    "utf8"
  )
    .split("\n")
    .filter((l) => l.trim());
  let checked = 0;
  let projectedCount = 0;
  for (const line of lines) {
    const row = JSON.parse(line);
    if (row._meta) continue;
    const pos = row.position ?? {};
    const coords = projectedCoordinates({
      source: pos.source,
      space: pos.space,
      x: typeof pos.x === "number" ? pos.x : undefined,
      y: typeof pos.y === "number" ? pos.y : undefined,
    });
    if (pos.source !== "inline" || pos.space !== "world-assumed") {
      assert.equal(coords, null, `row ${row.poi_id} must not project`);
    } else {
      assert.ok(coords, `World.positionSpawn-class row ${row.poi_id} projects`);
      projectedCount++;
    }
    checked++;
  }
  assert.ok(checked > 900, `expected the ~986-row corpus, saw ${checked}`);
  // today only World.positionSpawn cells carry world-assumed space; POIs are
  // pending-placement classes — the module renders zero markers honestly.
  assert.equal(projectedCount, 0);
});
