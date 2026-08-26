/*
 * TW-MV1 — AC MV-0.4 (A-MV1 F-1): the two-list family ledger law.
 *
 * Fixture half (always green offline): the §3.2(c) required partition is
 * lawful, and deliberately broken ledgers FAIL each sub-law — proving the
 * checker has teeth, not tautology.
 *
 * Live half ([M0-PENDING] prefixed): reconciles public/map/markers.json's
 * emitted `_meta` against FRESH recounts of poi-kinds.json + poi.jsonl
 * ("never inherited from v0 _meta"). Red until the M0 emitter rerun lands;
 * that redness IS the sequencing gate (spec §2 hard rule).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";
import {
  loadFixture,
  eligibleRecount,
  checkLedgerLaw,
  assignRowToFamilies,
  PACK_ROOT,
  SITE_DIR,
} from "./mapFixtures.mjs";

const SITE_ROOT = join(SITE_DIR, "..");

const fixture = loadFixture("ledger-ok.fixture.json");

function law(ledger, markerRowCount) {
  const { total, tally, levels } = eligibleRecount();
  return checkLedgerLaw(ledger, {
    eligibleTotal: total,
    tally,
    levels,
    declaredMarkerRowCount: markerRowCount,
  });
}

test("MV-0.4 fixture: the §3.2(c) required partition is lawful end-to-end", () => {
  assert.deepEqual(law(fixture, fixture.declared_marker_row_count), []);
});

test("MV-0.4 fixture: Σ poi_rows over pending_families = 709 = fresh eligible recount", () => {
  const sum = fixture.pending_families.reduce((a, f) => a + f.poi_rows, 0);
  assert.equal(sum, 709);
  assert.equal(eligibleRecount().total, 709, "fresh corpus recount must stay 709 while the spec freeze holds");
});

test("MV-0.4 fixture: each eligible row claimed by exactly one family (row-granular)", () => {
  // miniature pool spanning every family axis, incl the container-scoped
  // minigame siblings (level9 covered vs level1 no-carrier-edge)
  const pool = [
    { kind: "cartridge", class: "FlashTaker", level: "level9" },
    { kind: "cartridge", class: "TamagotchiGame_Cartridge", level: "level3" },
    { kind: "travel_gate", class: "Scene_Load", level: "level2" },
    { kind: "travel_gate", class: "Trigger_Teleport", level: "level5" },
    { kind: "travel_gate", class: "Player_Teleport", level: "level5" },
    { kind: "minigame_access", class: "MinigamesController", level: "level9" },
    { kind: "minigame_access", class: "MinigamesController", level: "level23" },
    { kind: "minigame_access", class: "MinigamesController", level: "level1" },
    { kind: "move_point", class: "MitaAIMovePoint", level: "level8" },
    { kind: "move_point", class: "Transform_Position", level: "level8" },
    { kind: "spawn_event", class: "Event_CreateResource", level: "level6" },
    { kind: "safe", class: "Basement_Safe", level: "level19" },
    { kind: "interactable", class: "ObjectInteractive", level: "level13" },
    { kind: "interactable", class: "Trigger_DistanceCircle", level: "level14" },
    { kind: "monster", class: "Mob_ChibiMita", level: "level10" },
  ];
  for (const row of pool) {
    const hits = assignRowToFamilies(row, fixture.pending_families);
    assert.equal(hits.length, 1, `${JSON.stringify(row)} claimed by [${hits.join(", ")}]`);
  }
});

test("MV-0.4 fixture teeth: broken partitions fail their specific sub-law", () => {
  const clone = () => JSON.parse(JSON.stringify(fixture));

  // (a) partition-sum drift
  let bad = clone();
  bad.pending_families[0].poi_rows = 22;
  assert.ok(law(bad, 70).some((v) => v.startsWith("(a)")), "sum drift must fail (a)");

  // (b) row double-claim without container scopes
  bad = clone();
  bad.pending_families.push({
    family_id: "sneaky/dup", poi_kinds: ["interactable"], poi_classes: ["ObjectInteractive"],
    poi_rows: 5, disposition: "deferred", reason_code: "x", unblock_owner: "y",
  });
  assert.ok(law(bad, 70).some((v) => v.includes("(b1)") || v.includes("(b2)")),
    "double-claim must fail coverage/disjointness");

  // (b) under-coverage: drop a family entirely
  bad = clone();
  bad.pending_families = bad.pending_families.filter((f) => f.family_id !== "safe");
  assert.ok(law(bad, 70).some((v) => v.includes("Basement_Safe") && v.includes("(b")),
    "dropped family must fail coverage");

  // (c) emitted total mismatch against markers data-row count
  bad = clone();
  assert.ok(law(bad, 69).some((v) => v.startsWith("(c)")), "emitted-total drift must fail (c)");

  // (d) deferred accountability
  bad = clone();
  delete bad.pending_families.find((f) => f.family_id === "safe").reason_code;
  assert.ok(law(bad, 70).some((v) => v.startsWith("(d)")), "deferred without reason_code must fail (d)");
  bad = clone();
  delete bad.pending_families.find((f) => f.family_id === "safe").unblock_owner;
  assert.ok(law(bad, 70).some((v) => v.startsWith("(d)")), "deferred without unblock_owner must fail (d)");

  // structural: bare-kind key (the v0 defect class), third disposition state,
  // placement families carrying poi fields / missing source_dataset
  bad = clone();
  bad.pending_families.push({ family_id: "bare", poi_kinds: ["safe"], poi_classes: [], poi_rows: 0, disposition: "deferred" });
  assert.ok(law(bad, 70).some((v) => v.includes("bare-kind key")));
  bad = clone();
  bad.pending_families[8].disposition = "pending";
  assert.ok(law(bad, 70).some((v) => v.includes("no third state") || v.includes("disposition")));
  bad = clone();
  bad.placement_families[0].poi_rows = 11;
  assert.ok(law(bad, 70).some((v) => v.includes("neither poi_rows nor poi_classes")));
  bad = clone();
  delete bad.placement_families[0].source_dataset;
  assert.ok(law(bad, 70).some((v) => v.includes("source_dataset")));
});

/* ------------------------------------------------------------------ */
/* Live reconciliation — RED until the M0 emitter lands markers.jsonl v2 */
/* ------------------------------------------------------------------ */

test("[M0-PENDING] MV-0.4 live: emitted _meta ledger reconciles with a fresh recount", async () => {
  const { readFileSync } = await import("node:fs");
  const { join } = await import("node:path");
  const artifact = JSON.parse(
    readFileSync(join(SITE_ROOT, "public", "map", "markers.json"), "utf8")
  );
  const meta = artifact._meta ?? {};
  const rows = artifact.rows ?? [];
  assert.ok(rows.length > 0, "AC MV-0.1: markers.jsonl ships >0 data rows (still the v0 zero-row artifact)");
  if (meta.row_count !== undefined) assert.equal(meta.row_count, rows.length);

  const pending = meta.pending_families ?? [];
  const placement = meta.placement_families ?? [];
  assert.ok(pending.length > 0, "_meta.pending_families[] missing — M0 ledger not written yet");
  assert.ok(placement.length > 0, "_meta.placement_families[] missing — placement-sourced markers not ledgered yet");

  const violations = law(
    { pending_families: pending, placement_families: placement },
    rows.length
  );
  assert.deepEqual(
    violations,
    [],
    `AC MV-0.4 ledger law violations against the LIVE emission:\n  ${violations.join("\n  ")}`
  );
});

test("[M0-PENDING] MV-0.2 live: position_dispositions total for the 76 pptr-unresolved rows", async () => {
  const { readFileSync } = await import("node:fs");
  const artifact = JSON.parse(
    readFileSync(join(SITE_ROOT, "public", "map", "markers.json"), "utf8")
  );
  const disp = artifact._meta?.position_dispositions;
  if (!disp) {
    assert.fail("_meta.position_dispositions missing — M0 disposition accounting not written yet");
  }
  // fresh recount of the pptr-unresolved pool from poi.jsonl
  const poiLines = readFileSync(join(PACK_ROOT, "extracted/data/scenes/poi.jsonl"), "utf8")
    .split("\n").filter((l) => l.trim());
  let unresolved = 0;
  for (const line of poiLines) {
    const row = JSON.parse(line);
    if ("_meta" in row) continue;
    if (row.position?.source === "pptr-unresolved") unresolved++;
  }
  const accounted =
    (disp["resolved-by-s9"] ?? 0) +
    Object.entries(disp)
      .filter(([k]) => k.startsWith("deferred"))
      .reduce((a, [, n]) => a + n, 0);
  assert.equal(accounted, unresolved,
    `_meta.position_dispositions accounts ${accounted} of ${unresolved} pptr-unresolved rows`);
  // no third state: every key is resolved-by-s9 or deferred:<reason>
  for (const key of Object.keys(disp)) {
    assert.match(key, /^(resolved-by-s9|deferred:.+)$/, `third disposition state "${key}"`);
  }
});
