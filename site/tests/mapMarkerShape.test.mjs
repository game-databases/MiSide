/*
 * TW-MV1 — marker shape contract (AC MV-0.3 schema matrix, AC MV-0.1 join
 * audit, §3.2(b) placement-sourced shape, registry v2 additivity).
 *
 * Fixture half: green offline, pins §4.1 + §3.2(b); negative mutants prove
 * each rule bites (fabricated join ids fail loudly per MV-0.1).
 *
 * Live half ([M0-PENDING]): the FULL emitted markers.json + registry.json are
 * asserted over every row (never sampled). Red until M0 lands.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  loadFixture,
  ownerIds,
  hostedMinigamesByContainer,
  sceneIds,
  validateMarkerRow,
  agreementViolations,
} from "./mapFixtures.mjs";

// routes.ts KIND_SEGMENT is the authority for routed segments; mirrored here
// (byte-checked against the real table in mapGates.test.mjs) so this file
// stays free of @-alias imports.
const ROUTED_SEGMENTS = {
  cartridges: "cartridges",
  profiles: "lore/profiles",
  minigames: "minigames",
};

function ctx() {
  return {
    routedSegments: ROUTED_SEGMENTS,
    ownerIds: ownerIds(),
    hostedMinigames: hostedMinigamesByContainer(),
  };
}

const fixtureRows = loadFixture("markers.fixture.json").rows;

test("MV-0.3 fixture: every §4.1/§3.2(b) row passes the full shape matrix", () => {
  for (const row of fixtureRows) {
    assert.deepEqual(validateMarkerRow(row, ctx()), [], `row ${row.marker_id}`);
    assert.deepEqual(agreementViolations(row), [], `row ${row.marker_id} MV-2 agreement`);
  }
});

test("§3.2(b) fixture: placement-sourced rows carry poi_id:null + scene granularity", () => {
  const placement = fixtureRows.filter((r) => r.placement_source);
  assert.equal(placement.length, 2, "fixture must cover both emitters (DS-5 + minigame carrier)");
  for (const row of placement) {
    assert.equal(row.poi_id, null, `${row.marker_id}: poi_id null mandatory`);
    assert.equal(row.position.status, "scene-granular");
    assert.ok(row.position.status !== "projected", "scene-granular rows never plot");
    assert.equal(typeof row.container, "string");
  }
});

test("§3.2(b) fixture: emitter-split scalar container; compound id banned downstream", () => {
  // the relink compound form is to:"scene-class-family@levelN" — a marker's
  // container field must be the SPLIT scalar, never the compound
  const bad = {
    ...fixtureRows[3],
    container: "scene-class-family@level9",
  };
  const v = validateMarkerRow(bad, ctx());
  assert.ok(v.some((x) => x.includes("compound id")), `compound container must fail: ${v.join("; ")}`);
});

test("§3.2(b) fixture: instance_census mandatory when a container hosts >1 minigame", () => {
  // level9 hosts 4 minigames over 3 controller rows (measured, spec §3.2(b)) —
  // a census of total:1 there would be a silent one-of-N
  const hosted = hostedMinigamesByContainer().get("level9");
  assert.equal(hosted.size, 4, "corpus drift: level9 minigame count changed — re-pin spec numbers");
  const bad = { ...fixtureRows[3], instance_census: { bare: 1, suffixed: 0, total: 1 } };
  const v = validateMarkerRow(bad, ctx());
  assert.ok(v.some((x) => x.includes("one-of-N")), `silent one-of-N must fail: ${v.join("; ")}`);
});

test("MV-0.1 fixture teeth: fabricated owning ids fail the join audit loudly", () => {
  const bad = {
    ...fixtureRows[0],
    entity_slug: "totally-fabricated-cartridge",
    links: { ...fixtureRows[0].links, page_url: "/cartridges/totally-fabricated-cartridge",
      focus_url: "/map?focus=cartridges:totally-fabricated-cartridge&scene=level9" },
  };
  const v = validateMarkerRow(bad, ctx());
  assert.ok(v.some((x) => x.includes("join audit FAIL")), `fabricated id must fail loudly: ${v.join("; ")}`);
});

test("MV-2 fixture teeth: status/projection disagreements fail both ways", () => {
  // claims projected, floats refuse
  let bad = {
    ...fixtureRows[0],
    marker_id: "mutant/refuses",
    position: { ...fixtureRows[0].position, source: "inline", space: "parent-local" },
  };
  assert.ok(agreementViolations(bad).length > 0, "projected claim with non-projecting cell must fail");

  // projects but does not claim it (inverse)
  bad = {
    ...fixtureRows[1],
    marker_id: "mutant/inverse",
    position: { ...fixtureRows[1].position, source: "inline", space: "world-assumed", x: 1.5, y: -2 },
  };
  assert.ok(
    agreementViolations(bad).some((v) => v.includes("inverse")),
    "projecting floats without a projected claim must fail"
  );

  // placement-sourced rows carry no projection inputs and are skipped by design
  assert.deepEqual(agreementViolations(fixtureRows[3]), []);
});

test("§4.1 fixture teeth: placement-sourced row with a poi anchor or plotted status fails", () => {
  let bad = { ...fixtureRows[3], poi_id: "level9:MinigamesController_#4242" };
  assert.ok(validateMarkerRow(bad, ctx()).some((x) => x.includes("poi_id:null")),
    "per-instance minigame anchoring must be ABSENT (OQ-7)");
  bad = { ...fixtureRows[3], position: { ...fixtureRows[3].position, status: "projected" } };
  assert.ok(validateMarkerRow(bad, ctx()).some((x) => x.includes("scene-granular")),
    "scene-granular marker rendered as plotted pin must fail");
  bad = { ...fixtureRows[2], instance_census: undefined };
  assert.ok(validateMarkerRow(bad, ctx()).some((x) => x.includes("instance_census")),
    "missing census must fail");
});

/* ------------------------------------------------------------------ */
/* Live artifacts — RED until M0 lands                                 */
/* ------------------------------------------------------------------ */

async function loadPublicJson(name) {
  const { readFileSync } = await import("node:fs");
  const { join } = await import("node:path");
  return JSON.parse(readFileSync(join(process.cwd(), "public", "map", name), "utf8"));
}

test("[M0-PENDING] MV-0.3 live: full-file schema matrix over markers.json (not sampled)", async () => {
  const artifact = await loadPublicJson("markers.json");
  const rows = artifact.rows ?? [];
  assert.ok(rows.length > 0, "markers.json still v0 (zero rows) — M0 emission pending");

  // AC MV-0.3: marker ids AND poi anchors unique; matrix over EVERY row
  const markerIds = new Set();
  const poiIds = new Set();
  const all = [];
  for (const row of rows) {
    all.push(...validateMarkerRow(row, ctx()), ...agreementViolations(row));
    if (row.marker_id != null) {
      assert.ok(!markerIds.has(row.marker_id), `duplicate marker_id ${row.marker_id}`);
      markerIds.add(row.marker_id);
    }
    if (typeof row.poi_id === "string") {
      assert.ok(!poiIds.has(row.poi_id), `duplicate poi anchor ${row.poi_id} (instance identity lost)`);
      poiIds.add(row.poi_id);
    }
  }
  assert.deepEqual(all, [], `schema/join violations in live emission:\n  ${all.join("\n  ")}`);
});

test("[M0-PENDING] live: profile rows carry DS-5 placement verbatim", async () => {
  const artifact = await loadPublicJson("markers.json");
  const profiles = (artifact.rows ?? []).filter((r) => r.placement_source === "DS-5");
  assert.ok(profiles.length > 0 && profiles.length <= 11, `expected ≤11 profile rows, saw ${profiles.length}`);
  for (const row of profiles) {
    for (const key of ["carrier_class", "component_path_id", "container"]) {
      assert.ok(row.placement?.[key] !== undefined, `${row.marker_id}: placement.${key} missing (must ride verbatim)`);
    }
  }
});

test("registry: v1 fields survive + switcher totality data-side (24 scenes)", async () => {
  const registry = await loadPublicJson("registry.json");
  const ids = registry.map((e) => e.scene_id);
  assert.deepEqual([...ids].sort(), [...sceneIds()].sort(), "registry scenes must equal scenes.jsonl exactly");
  for (const e of registry) {
    // v1 fields that must survive v2 additively (spec §3.2(d))
    assert.ok(Array.isArray(e.zoom) && e.zoom.length === 2, `${e.scene_id}: zoom pair missing`);
    assert.equal(e["coordinate-transform"], "rect-per-map");
    assert.equal(e.imagery, "authored");
    assert.ok("bounds" in e, `${e.scene_id}: bounds key missing`);
    assert.ok(
      e.bounds === null ||
        (Array.isArray(e.bounds) && e.bounds.every((n) => typeof n === "number") && e.bounds.length === 4),
      `${e.scene_id}: bounds neither null nor [4 numbers] — bounding guesses are forbidden`
    );
  }
});

test("[M0-PENDING] registry v2: display_label_loc + role + status + per-kind counts", async () => {
  const registry = await loadPublicJson("registry.json");
  for (const e of registry) {
    assert.ok("display_label_loc" in e, `${e.scene_id}: display_label_loc pointer missing (explicit null allowed)`);
    assert.ok(typeof e.role === "string", `${e.scene_id}: role missing`);
    assert.ok(
      e.status === "awaiting-artwork" || e.status === "ready",
      `${e.scene_id}: status must be awaiting-artwork|ready`
    );
    const countKeys = ["per_kind", "per_kind_marker_counts", "marker_counts", "kinds", "counts_by_kind"];
    assert.ok(
      countKeys.some((k) => e[k] !== undefined && typeof e[k] === "object"),
      `${e.scene_id}: per-kind marker counts missing (looked for ${countKeys.join("|")})`
    );
    // progressive artwork flip: no authored schematic ⇒ honest awaiting state
    const { existsSync } = await import("node:fs");
    const { join } = await import("node:path");
    const hasArt = existsSync(join(process.cwd(), "public", "map", e.scene_id, "base.svg"));
    if (!hasArt) assert.equal(e.status, "awaiting-artwork", `${e.scene_id}: no base.svg yet — status must stay awaiting-artwork`);
  }
});
