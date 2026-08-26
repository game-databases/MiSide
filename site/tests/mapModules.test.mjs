/*
 * TW-MV1 — viewer module contracts (AC MV-1 render-partition, PinPopover
 * provenance echo + crawlable link, M4 from:null census bar, zero-markers
 * graceful state).
 *
 * Node's type-stripping cannot execute JSX, so DOM proofs stay in the
 * scripted-trace lane. What IS automated here:
 *  - the REAL server partition (routes/mapView.sceneMarkers) exercised over a
 *    fixture markers.jsonl via a temp MISIDE_EXTRACTED_ROOT — plotted pin vs
 *    awaiting-transform chip vs scene-granular list entry, incl. the MV-2
 *    fail-safe ceiling;
 *  - the REAL contracts.characterSceneEdges reader against the live relink —
 *    from:null scene-class census rows must never reach per-entity modules;
 *  - static greps (the spec's own "static grep" proof class) for the popover
 *    carry law and honest-empty rendering.
 */
import "./registerAliasLoader.mjs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdirSync, writeFileSync, rmSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { loadFixture } from "./mapFixtures.mjs";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = join(SITE_DIR, "..");
const MAP_DIR = join(SITE_ROOT, "src", "components", "map");

process.env.MISIDE_EXTRACTED_ROOT ??= join(SITE_ROOT, "..", "extracted");

function readMapComponent(name) {
  const p = join(MAP_DIR, name);
  return existsSync(p) ? readFileSync(p, "utf8") : null;
}

/* ---------- MV-1: the real render partition over fixture markers ---------- */

/** Materialize fixture rows as a markers.jsonl under a temp extracted root. */
function withTempMarkers(rows, fn) {
  const root = join(SITE_ROOT, "tmp", `mv1-pipeline-${process.pid}`);
  mkdirSync(join(root, "data", "scenes"), { recursive: true });
  const meta = JSON.stringify({
    _meta: {
      schema: "tw-mv1.fixture/markers",
      row_count: rows.length,
      note: "TW-MV1 FIXTURE — synthetic §4.1 rows for the render-partition test",
    },
  });
  writeFileSync(
    join(root, "data", "scenes", "markers.jsonl"),
    [meta, ...rows.map((r) => JSON.stringify(r))].join("\n") + "\n"
  );
  const prev = process.env.MISIDE_EXTRACTED_ROOT;
  process.env.MISIDE_EXTRACTED_ROOT = root;
  try {
    return fn();
  } finally {
    process.env.MISIDE_EXTRACTED_ROOT = prev;
    rmSync(root, { recursive: true, force: true });
  }
}

test("[MV-1] sceneMarkers partitions pins / pending / granular exactly by projection truth", async () => {
  const { sceneMarkers } = await import("@/components/routes/mapView.ts");
  const rows = loadFixture("markers.fixture.json").rows;
  // the DS-5 profile row (level17) and the awaiting cartridge row (level12)
  // are rebound so ONE scene holds the full disposition axis
  rows[1].placement.scene_binding = "level9";
  rows[2].placement.scene_binding = "level9";

  const vm = withTempMarkers(rows, () => sceneMarkers("level9", "", "en"));
  assert.equal(vm.pins.length, 1, "only the projected∧projecting row may plot");
  assert.equal(vm.pins[0].markerId, rows[0].marker_id);
  assert.equal(vm.pending.length, 1, "awaiting-transform-stage renders as a chip, never a pin");
  assert.equal(vm.pending[0].markerId, rows[1].marker_id);
  assert.equal(vm.granular.length, 2, "placement-sourced scene-granular rows are list entries");
  assert.deepEqual(
    vm.granular.map((g) => g.markerId).sort(),
    [rows[2].marker_id, rows[3].marker_id]
  );
  // provenance rides through to the VMs (popover echo substrate)
  assert.equal(vm.pins[0].mechanism, "hard");
  assert.equal(vm.granular[0].mechanism ?? vm.granular[1].mechanism, "hard");
});

test("[MV-1/MV-2] fail-safe ceiling: a projected CLAIM without projecting floats never plots", async () => {
  const { sceneMarkers } = await import("@/components/routes/mapView.ts");
  const bad = {
    ...loadFixture("markers.fixture.json").rows[0],
    marker_id: "mutant/empty-floats",
    position: { ...loadFixture("markers.fixture.json").rows[0].position, x: null, y: null },
  };
  const vm = withTempMarkers([bad], () => sceneMarkers("level9", "", "en"));
  assert.equal(vm.pins.length, 0, "disagreement row may NEVER plot (ceiling below the emitted claim)");
  assert.equal(vm.pending.length, 1);
});

test("[MV-1] zero-markers graceful state: empty markers.jsonl yields empty buckets, no crash", async () => {
  const { sceneMarkers } = await import("@/components/routes/mapView.ts");
  const vm = withTempMarkers([], () => sceneMarkers("level9", "", "en"));
  assert.deepEqual(vm, { pins: [], pending: [], granular: [] });
});

test("zero-markers graceful state: the island keeps an explicit-empty well branch (static grep)", () => {
  const src = readMapComponent("SceneMap.tsx");
  assert.ok(src, "SceneMap.tsx missing");
  assert.match(src, /VoidWell/, "the schematic-grid VoidWell is the awaiting-artwork state (§8)");
  assert.match(src, /pendingLabel|granularLabel|pendingCount|granularCount/,
    "non-plotted dispositions must render as visible counted states, not vanish");
  assert.doesNotMatch(src, /https?:\/\/(?!localhost)[^\s"'`]+\.(png|svg|webp)/i,
    "no remote imagery — owned artifacts only (negative-gate posture)");
});

test("[M4] census bar: characterSceneEdges drops every from:null census row, keeps slugged edges", async () => {
  const { characterSceneEdges } = await import("@/data/contracts.ts");
  const edges = characterSceneEdges();
  // corpus fact (spec §7): 12 direction rows → 4 forward slugged edges
  // (mita-black ×2, mita-core ×2); the 4 from:null scene-class censuses and
  // inverses must never surface as per-entity facts
  assert.ok(edges.length > 0 && edges.every((e) => typeof e.from === "string"),
    "from:null census rows leaked into per-entity module data");
  for (const census of ["MitaPerson", "MitaKiller", "MitaFreak Enter", "Mob_ChibiMita"]) {
    assert.ok(!edges.some((e) => e.from.includes(census)),
      `${census} census row reached per-entity modules (rendering a container census per-entity is prohibited)`);
  }
  assert.ok(edges.some((e) => e.from === "mita-black" && e.status === "modeled"),
    "slugged inferred edges must survive the bar — they render WITH surfaced provenance");
});

test("[MV-5 slice] switcherGroups: 24 scenes total; unlabeled = the 5 chapter-less levels; role groups intact", async () => {
  const { switcherGroups } = await import("@/components/routes/mapView.ts");
  const groups = switcherGroups("en", "Unlabeled");
  const all = groups.flatMap((g) => g.scenes);
  assert.equal(all.length, 24, "switcher totality: every scene listed");
  assert.deepEqual(
    [...new Set(all.map((s) => s.scene_id))].length,
    24,
    "duplicate scene in switcher"
  );
  const unlabeled = groups.find((g) => g.id === "unlabeled");
  assert.ok(unlabeled, "chapter-less story levels must group as unlabeled (never a guessed chapter)");
  assert.deepEqual(
    unlabeled.scenes.map((s) => s.scene_id).sort(),
    ["level12", "level15", "level18", "level3", "level7"],
    "unlabeled group must be exactly levels 3/7/12/15/18 (spec §7)"
  );
  for (const role of ["boot", "title", "menu", "unbound"]) {
    const g = groups.find((x) => x.id === role);
    assert.ok(g && g.scenes.length === 1 && g.lcd, `role group ${role} must exist as an LCD singleton`);
  }
});

/* ---------------- static greps ---------------- */

test("§5 component inventory exists (SceneSwitcher/KindFilter/PinPopover/LockedCell)", () => {
  const missing = ["SceneSwitcher.tsx", "KindFilter.tsx", "PinPopover.tsx", "LockedCell.tsx"].filter(
    (f) => !readMapComponent(f)
  );
  assert.deepEqual(missing, [], `missing M2 components: ${missing.join(", ")}`);
});

test("PinPopover carry law: evidence-classed source echoed verbatim + crawlable <a> (static grep)", () => {
  const src = readMapComponent("PinPopover.tsx");
  assert.ok(src, "PinPopover.tsx missing");
  // the surfacing condition bites on any non-hard mechanism (F-7)
  assert.match(src, /mechanism\s*!==\s*["']hard["']/,
    "provenance cell must surface whenever mechanism !== hard");
  assert.match(src, /\{target\.mechanism\}/, "mechanism value must be echoed verbatim");
  assert.match(src, /\{target\.sourceJoin\}|sourceJoin/, "source_join rides beside it");
  assert.match(src, /<a\b/, "entity link must be a real anchor");
  assert.match(src, /href=\{target\.pageHref\}/, "anchor href must be the emitter-written page path");
  // machine-voice status register for non-plotted rows (LCD discipline)
  assert.match(src, /scene-granular[\s\S]*awaiting-transform-stage|awaiting-transform-stage[\s\S]*scene-granular/,
    "status token register must distinguish the two non-pin dispositions");
});
