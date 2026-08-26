/*
 * TW-MV1 — projection correctness on KNOWN coordinates + OQ-6 null-bounds
 * posture (AC MV-2 corpus side; the conjunction-gate totality table itself
 * already lives in mapAxis.test.mjs and is not duplicated here).
 *
 * Spec pins (§0.2 / §4.2 / OQ-6 ruling):
 *  - exactly 20 story-scene spawns are the projecting cell today
 *    (measured extents x −27.75…11.25, y −3…12, z −108.5…5.5);
 *  - CRS.Simple plots RAW world coords — presentation math must not mutate
 *    them;
 *  - fit-to-bounds activates ONLY when the registry carries bounds;
 *    bounds:null is accepted indefinitely with the deterministic mean-center
 *    fallback over plotted points (presentation math over consumed rows —
 *    allowed; it derives no data).
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
import { storySpawns } from "./mapFixtures.mjs";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));

test("known coordinates pass through untouched (CRS.Simple raw world coords)", () => {
  // corner values of the spec's measured envelope + an interior point
  const known = [
    [-27.75, -3, -108.5],
    [11.25, 12, 5.5],
    [0.56, 0, -0.38],
    [-6.172363, 1.25, 3.5],
  ];
  for (const [x, y, z] of known) {
    assert.deepEqual(projectedCoordinates({ source: "inline", space: "world-assumed", x, y, z }), { x, y, z });
    assert.deepEqual(placementDecision({ source: "inline", space: "world-assumed" }).disposition, "PROJECTED");
  }
});

test("the 20 story spawns project; extents match the spec's measured envelope", () => {
  const spawns = storySpawns();
  assert.equal(spawns.length, 20, "corpus drift: story-spawn count changed — re-pin spec §0.2 numbers");
  const xs = spawns.map((s) => s.x);
  const ys = spawns.map((s) => s.y);
  const zs = spawns.map((s) => s.z);
  assert.equal(Math.min(...xs), -27.75);
  assert.equal(Math.max(...xs), 11.25);
  assert.equal(Math.min(...ys), -3);
  assert.equal(Math.max(...ys), 12);
  assert.equal(Math.min(...zs), -108.5);
  assert.equal(Math.max(...zs), 5.5);
  for (const s of spawns) {
    const coords = projectedCoordinates({
      source: s.source, space: s.space, x: s.x, y: s.y, z: s.z,
    });
    assert.ok(coords, `${s.scene_id} spawn must project`);
    assert.equal(coords.x, s.x);
    assert.equal(coords.y, s.y);
  }
});

test("MV-1 unit core: a PENDING-disposition row never plots even with plausible floats", () => {
  // pptr-unresolved carrier transform pointer unresolved — floats absent by
  // construction, and even if present the conjunction refuses the cell
  assert.equal(projectedCoordinates({ source: "pptr-unresolved", space: "world-assumed", x: 1, y: 2 }), null);
  assert.equal(projectedCoordinates({ source: "inline", space: "unknown", x: 1, y: 2 }), null);
  assert.equal(
    placementDecision({ source: "none" }).disposition, "PENDING"
  );
});

test("[OQ-6] null bounds accepted indefinitely: fit/imagery only behind a truthy-bounds guard; deterministic mean-center fallback present", () => {
  const src = readFileSync(join(SITE_DIR, "..", "src/components/map/SceneMap.tsx"), "utf8");
  const lines = src.split("\n");
  // every fitBounds usage must sit inside a guard that tests bounds itself
  const fitLines = lines.reduce((acc, line, i) => {
    if (/\.fitBounds\(/.test(line.replace(/\/\/.*$/, ""))) acc.push(i);
    return acc;
  }, []);
  assert.ok(fitLines.length > 0, "expected at least one guarded fit-to-bounds path once calibration lands");
  for (const i of fitLines) {
    const window = lines.slice(Math.max(0, i - 8), i + 2).join("\n");
    assert.match(
      window,
      /\bif\s*\(\s*[\w.!.]*bounds\b|bounds\s*(&&|\?\?|\?|!==\s*null)/,
      `fitBounds at line ${i + 1} is not visibly guarded by non-null bounds — OQ-6 requires bounds:null accepted indefinitely`
    );
  }
  // the fallback branch: plain arithmetic mean of plotted points, finite when empty
  assert.match(src, /pins\.length > 0 \? pins\.reduce\(\(s, p\) => s \+ p\.[xy], 0\) \/ pins\.length : 0/,
    "the deterministic mean-center fallback (mean of plotted points, [0,0]-safe when empty) must stay present (OQ-6)");
});

test("[OQ-6] imagery overlays ONLY over calibrated bounds (never a faked coordinate frame)", () => {
  const src = readFileSync(join(SITE_DIR, "..", "src/components/map/SceneMap.tsx"), "utf8");
  assert.match(src, /base\.svg/, "authored schematic contract path must be referenced");
  const overlay = src.indexOf("imageOverlay") >= 0 ? src.indexOf("imageOverlay") : src.search(/SVG\)|addTo\(map\)/);
  if (/imageOverlay/.test(src)) {
    const before = src.slice(Math.max(0, src.indexOf("imageOverlay") - 400), src.indexOf("imageOverlay"));
    assert.match(before, /!?\s*bounds|if \(!map \|\| !bounds\)/, "image overlay must be gated on calibrated bounds");
  }
});
