/*
 * F-MV4 — visual-critic fix round for the scene-map surface
 * (docs/research/visual-critic-map.mdx fixes 1, 2, 3 + the i18n/microcopy
 * wave). Node's type-stripping cannot execute JSX, so render proofs stay in
 * the scripted-trace lane; what IS pinned here:
 *   - FMV4-A/B/C/D static laws over the island sources (filter-over-displayed,
 *     full popstate resync, in-panel LockedCells with working popover
 *     triggers, no bounds/imagery gate in front of the rows);
 *   - functional units for the chrome label plumbing (mapChromeStrings,
 *     switcherGroups role groups);
 *   - the ×34 chrome keyset for every new map.kind/map.role/map.census key,
 *     including the ar RTL leg;
 *   - the one-locations-tab merge on the entity route.
 */
import "./registerAliasLoader.mjs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MAP_DIR = join(SITE_ROOT, "src", "components", "map");
const CHROME_DIR = join(SITE_ROOT, "src", "i18n", "chrome");

process.env.MISIDE_EXTRACTED_ROOT ??= join(SITE_ROOT, "..", "extracted");

function readSrc(rel) {
  return readFileSync(join(SITE_ROOT, rel), "utf8");
}
function readMap(name) {
  return readFileSync(join(MAP_DIR, name), "utf8");
}

/* ---------- FMV4-A filters gate EVERY displayed row ---------- */

test("[FMV4-A] filter law: pending + granular rows pass isEnabled/matchesQuery like pins", () => {
  const src = readMap("MapViewer.tsx");
  // three filtered buckets exist, each gated by BOTH predicates
  for (const bucket of ["visiblePins", "visiblePending", "visibleGranular"]) {
    assert.ok(
      src.includes(`const ${bucket} = React.useMemo`),
      `${bucket} memo missing`
    );
  }
  assert.match(
    src,
    /vm\.pending\.filter\(\(c\) => isEnabled\(c\.kind\) && matchesQuery\(c\.title\)\)/,
    "deferred pending rows must pass the same filter predicates as pins"
  );
  assert.match(
    src,
    /vm\.granular\.filter\(\(c\) => isEnabled\(c\.kind\) && matchesQuery\(c\.title\)\)/,
    "scene-granular rows must pass the same filter predicates as pins"
  );
});

test("[FMV4-A] quicksearch LCD counts ALL displayed rows — '0 shown' can never contradict the list", () => {
  const src = readMap("MapViewer.tsx");
  assert.match(
    src,
    /shownCount\s*=\s*visiblePins\.length \+ visiblePending\.length \+ visibleGranular\.length/,
    "LCD count must sum every visible disposition"
  );
  assert.match(src, /\{shownCount\} \{chromeStrings\.resultsCount\}/);
  assert.doesNotMatch(src, /\{visiblePins\.length\} \{chromeStrings\.resultsCount\}/,
    "pins-only count is the false-statement defect this law kills");
});

test("[FMV4-A] no unfiltered row stack anywhere; plotted pins keep their SSR anchor pills", () => {
  const src = readMap("MapViewer.tsx");
  // every surviving row RENDER path consumes a FILTERED bucket (the
  // selectedTarget lookup over vm.* is a data access, not a render list)
  assert.doesNotMatch(src, /\[\.\.\.vm\.(pending|granular)\]\.map/, "unfiltered deferred render list leaked back");
  assert.match(src, /visiblePins\.length > 0 && \(/, "plotted pins keep their crawlable anchor pills");
});

test("[FMV4-H] one-row law: deferred rows render once — in-panel cells ARE the anchors", () => {
  const viewer = readMap("MapViewer.tsx");
  assert.ok(
    !/visiblePending\.map|visibleGranular\.map/.test(viewer),
    "a second deferred chip stack below the panel duplicates every row"
  );
  const locked = readMap("LockedCell.tsx");
  assert.match(locked, /<a\b/, "cell must be an anchor so the row is crawlable");
  assert.match(locked, /href=\{cell\.pageHref \?\? undefined\}/);
  assert.match(locked, /onOpen\(cell\.markerId\)/, "plain click opens the popover");
  assert.match(locked, /e\.preventDefault\(\)/, "navigation must not fight the popover");
});

/* ---------- FMV4-B popstate fully re-syncs ---------- */

test("[FMV4-B] popstate restores the DEFAULT scene when the URL carries no usable ?scene=", () => {
  const src = readMap("MapViewer.tsx");
  const pop = src.slice(src.indexOf("const onPop"), src.indexOf("window.addEventListener"));
  assert.ok(pop.length > 0, "onPop handler not found");
  assert.match(
    pop,
    /st\.scene && sceneIds\.includes\(st\.scene\) \? st\.scene : initialSceneId/,
    "Back to bare /map must land the select back on the default scene"
  );
  // kinds + focus reset legs stay intact
  assert.match(pop, /st\.kinds \? new Set\(st\.kinds\) : null/);
  assert.match(pop, /st\.focus \? \{ kind: st\.focus\.kind, slug: st\.focus\.slug \} : null/);
});

/* ---------- FMV4-C/D the scene's own rows render INSIDE the panel ---------- */

test("[FMV4-C] non-plotted rows render in-panel without any bounds/imagery gate", () => {
  const src = readMap("SceneMap.tsx");
  assert.match(src, /cells\.map\(\(c, i\) => \(|cells\.map\(\(c, i\) =>\s*\(/, "per-row LockedCell strip missing");
  assert.doesNotMatch(
    src,
    /bounds !== null && imageryReady && (pending|granular)/,
    "the bounds+imagery gate that made LockedCells unreachable must stay dead"
  );
  assert.match(
    src,
    /pins\.length === 0 && cells\.length === 0/,
    "VoidWell only for scenes with NO row of ANY disposition"
  );
});

test("[FMV4-D] every in-panel cell is a working popover trigger (provenance cell reachable)", () => {
  const locked = readMap("LockedCell.tsx");
  assert.match(locked, /onOpen\(cell\.markerId\)/, "plain click opens the popover");
  assert.match(locked, /e\.preventDefault\(\)/, "click must not navigate away from the popover");
  assert.match(locked, /data-slot="locked-cell"/);
  assert.match(locked, /min-h-11/, "≥44 px target");

  const scene = readMap("SceneMap.tsx");
  assert.match(scene, /onOpen=\{onSelectPin\}/, "cell trigger wires into the viewer selection");
  assert.match(scene, /selectedCell/, "cell-anchored popover placement exists");

  // the viewer resolves cells into PopoverTargets carrying mechanism/status/census
  const viewer = readMap("MapViewer.tsx");
  assert.match(viewer, /popoverFromCell/, "cell→popover conversion retained");
  assert.match(viewer, /instanceCensus/, "census rides the target");
});

test("[FMV4-E] status register is localized in BOTH dispositions — no hardcoded machine token beside copy", () => {
  const scene = readMap("SceneMap.tsx");
  // the strip maps each row's disposition to its chrome string
  assert.match(
    scene,
    /c\.status === "scene-granular" \? granularLabel : pendingLabel/,
    "in-panel cells pick the localized status per disposition"
  );
  const locked = readMap("LockedCell.tsx");
  assert.match(locked, /\{statusLabel\}/, "the cell prints the localized status word");
  const viewer = readMap("MapViewer.tsx");
  assert.ok(!/"awaiting-transform-stage"/.test(viewer.split("popoverFromCell")[0]) ||
    !/LcdTerminal[\s\S]{0,200}awaiting-transform-stage/.test(viewer),
    "no raw English status token rendered as copy");
});

/* ---------- FMV4-E microcopy: no raw vocabulary as copy ---------- */

test("[FMV4-E] kind chips, popover kind chip and POI headers print chrome-keyed labels", () => {
  assert.match(readMap("KindFilter.tsx"), /\{kindLabels\[kind\] \?\? kind\}/);
  assert.match(readMap("PinPopover.tsx"), /\{kindLabels\[target\.kind\] \?\? target\.kind\}/);
  const route = readSrc("src/components/routes/EntityDetailRoute.tsx");
  assert.match(route, /chromeStrings\.kindLabels\[g\.kind\] \?\? g\.kind/, "location POI group header localized");
});

test("[FMV4-E] instance census prints legend labels — emitter words never render raw", () => {
  assert.match(
    readMap("PinPopover.tsx"),
    /\{censusLabels\[k\] \?\? k\}: \{v\}/,
    "popover census chips ride the chrome legend"
  );
  assert.match(
    readSrc("src/components/entity/LocationModule.tsx"),
    /\{censusLabels\?\.\[k\] \?\? k\}: \{v\}/,
    "entity-page census chips ride the chrome legend"
  );
});

test("[FMV4-E] focus chip prints the entity's loc-correct title; raw key stays on title/aria", () => {
  const viewer = readMap("MapViewer.tsx");
  const chip = viewer.slice(viewer.indexOf("{focus && ("), viewer.indexOf("</button>", viewer.indexOf("{focus && (")));
  assert.match(chip, /focusedRow\?\.title/, "chip text is markerTitle()");
  assert.match(chip, /title=\{`\$\{focus\.kind\}:\$\{focus\.slug\}`\}/);
});

test("[FMV4-F] switcher role groups take chrome-keyed labels (boot/title/menu/unbound)", async () => {
  const { switcherGroups } = await import("@/components/routes/mapView.ts");
  const groups = switcherGroups("en", "Unlabeled", {
    boot: "Boot",
    title: "Title screen",
    menu: "Menu",
    unbound: "No chapter",
  });
  for (const [role, want] of [
    ["boot", "Boot"],
    ["title", "Title screen"],
    ["menu", "Menu"],
    ["unbound", "No chapter"],
  ]) {
    const g = groups.find((x) => x.id === role);
    assert.ok(g, `role group ${role} missing`);
    assert.equal(g.label, want, `role group ${role} must render its chrome label`);
    assert.notEqual(g.label, role, `role token "${role}" must never be the copy`);
  }
});

test("[FMV4-F] mapChromeStrings builds kind/role/census label maps; absent keys fall back to the token", async () => {
  const { mapChromeStrings } = await import("@/components/routes/mapView.ts");
  const s = mapChromeStrings({
    "map.kind.cartridge": "Cartridges",
    "map.role.boot": "Boot",
    "map.census.total": "Copies in scene",
    "map.chapterUnlabeled": "Unlabeled",
  });
  assert.equal(s.kindLabels.cartridge, "Cartridges");
  assert.equal(s.kindLabels.minigame_access, undefined, "unauthored key must be absent so callers fall back");
  assert.equal(s.roleLabels.boot, "Boot");
  assert.equal(s.censusLabels.total, "Copies in scene");
  assert.equal(s.censusLabels["minigames_hosted"], undefined);
});

/* ---------- FMV4-G the ×34 chrome keyset ---------- */

export const FMV4_KEYS = [
  "map.kind.cartridge","map.kind.profile_document","map.kind.minigame_access",
  "map.kind.safe","map.kind.travel_gate","map.kind.monster",
  "map.kind.interactable","map.kind.move_point","map.kind.spawn_event","map.kind.other",
  "map.role.boot","map.role.title","map.role.menu","map.role.unbound",
  "map.census.bare","map.census.suffixed","map.census.total","map.census.hosted",
];

test("[FMV4-G] every new map.* key exists, non-empty, across ×34 locales incl aliases", () => {
  const files = readdirSync(CHROME_DIR).filter((f) => f.endsWith(".json")).sort();
  assert.equal(files.length, 34);
  const missing = [];
  const empty = [];
  for (const f of files) {
    const obj = JSON.parse(readFileSync(join(CHROME_DIR, f), "utf8"));
    for (const key of FMV4_KEYS) {
      if (!(key in obj)) missing.push(`${f}:${key}`);
      else if (typeof obj[key] !== "string" || obj[key].trim().length === 0) empty.push(`${f}:${key}`);
    }
  }
  assert.deepEqual(missing, [], `missing:\n  ${missing.join("\n  ")}`);
  assert.deepEqual(empty, [], `empty:\n  ${empty.join("\n  ")}`);
});

test("[FMV4-G] ar leg: the new map keys carry real Arabic script (RTL data-side)", () => {
  const ar = JSON.parse(readFileSync(join(CHROME_DIR, "ar.json"), "utf8"));
  const arabic = /[؀-ۿ]/;
  let withScript = 0;
  for (const key of FMV4_KEYS) {
    const v = ar[key];
    assert.ok(!/^[\x00-\x7F]*$/.test(v), `ar.json:${key} is bare ASCII passthrough ("${v}")`);
    if (arabic.test(v)) withScript++;
  }
  assert.ok(
    withScript >= Math.ceil(FMV4_KEYS.length * 0.75),
    `only ${withScript}/${FMV4_KEYS.length} ar keys carry Arabic script`
  );
});

/* ---------- FMV4-H one locations-bearing tab per entity page ---------- */

test("[FMV4-H] duplicate Locations tabs collapsed: found-in + appearances ModuleLists are gone", () => {
  const route = readSrc("src/components/routes/EntityDetailRoute.tsx");
  assert.ok(!route.includes('id: "found-in"'), 'cartridge "found-in" duplicate tab survived');
  assert.ok(!route.includes('id: "appearances"'), 'character "appearances" duplicate tab survived');
  // the surviving location module carries the count + census legend
  assert.match(route, /tabLabel\(chrome\["nav.locations"\], refs\.length\)/);
  assert.match(route, /censusLabels=\{mapChromeStrings\(chrome\)\.censusLabels\}/);
});
