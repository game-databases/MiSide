/*
 * TW-MV1 shared law-checkers + fixture loader for the map-viewer suite
 * (docs/specs/map-viewer.mdx, frozen 2026-08-26).
 *
 * This module is test-support only (not matched by `node --test
 * tests/*.test.mjs`). It contains NO production imports except the projection
 * module, which is alias-free and already imported directly by mapAxis.test.mjs.
 *
 * Fixture files live in tests/fixtures/map-viewer/*.fixture.json and are
 * marked `_fixture: true`; they are synthetic §-shape transcriptions, never
 * corpus rows.
 */
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  projectedCoordinates,
  markerStatusDisagrees,
} from "../src/components/map/projection.ts";

export const SITE_DIR = dirname(fileURLToPath(import.meta.url));
export const PACK_ROOT = join(SITE_DIR, "..", "..");
export const FIXTURE_DIR = join(SITE_DIR, "fixtures", "map-viewer");

export function loadFixture(name) {
  return JSON.parse(
    readFileSync(join(FIXTURE_DIR, name), "utf8")
  );
}

/* ------------------------------------------------------------------ */
/* Corpus recounts (fresh from poi-kinds.json + poi.jsonl, per AC      */
/* MV-0.4's "never inherited from v0 _meta" law)                       */
/* ------------------------------------------------------------------ */

function jsonlRows(relPath) {
  return readFileSync(join(PACK_ROOT, relPath), "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l))
    .filter((r) => !("_meta" in r));
}

/** Fresh marker_eligible recount: { total, tally, levels } with tally keyed
 *  "kind|class" and levels: Map class -> Map(level -> row count). */
export function eligibleRecount() {
  const rulings = JSON.parse(
    readFileSync(join(PACK_ROOT, "extracted/data/scenes/poi-kinds.json"), "utf8")
  );
  const eligibleKindOf = new Map(
    rulings.classes.filter((c) => c.marker_eligible).map((c) => [c.class, c.kind])
  );
  const tally = new Map();
  const levels = new Map();
  let total = 0;
  for (const row of jsonlRows("extracted/data/scenes/poi.jsonl")) {
    const kind = eligibleKindOf.get(row.class);
    if (!kind) continue;
    const key = `${kind}|${row.class}`;
    tally.set(key, (tally.get(key) ?? 0) + 1);
    if (!levels.has(row.class)) levels.set(row.class, new Map());
    const byLvl = levels.get(row.class);
    byLvl.set(row.level, (byLvl.get(row.level) ?? 0) + 1);
    total++;
  }
  return { total, tally, levels };
}

/** Owning-dataset id sets for the AC MV-0.1 join audit. */
export function ownerIds() {
  const ids = (relPath, field) =>
    jsonlRows(relPath).map((r) => String(r[field]));
  return {
    cartridges: new Set(ids("extracted/data/cartridges/cartridges.jsonl", "cartridge_id")),
    profiles: new Set(ids("extracted/data/documents/profile_documents.jsonl", "document_id")),
    minigames: new Set(ids("extracted/data/cartridges/minigames.jsonl", "minigame_id")),
  };
}

/** Containers (levelN) hosting >1 minigame per the carrier relink inverse edges. */
export function hostedMinigamesByContainer() {
  const rows = jsonlRows("extracted/relinks/minigame--scene-carrier.jsonl");
  const out = new Map();
  for (const r of rows) {
    if (r.direction !== "inverse") continue;
    if (typeof r.from !== "string" || !r.from.startsWith("scene-class-family@")) continue;
    if (typeof r.to !== "string" || !r.to.startsWith("minigame:")) continue;
    const container = r.from.slice("scene-class-family@".length);
    const set = out.get(container) ?? new Set();
    set.add(r.to.slice("minigame:".length));
    out.set(container, set);
  }
  return out;
}

/** scene_id set from scenes.jsonl (24 rows incl boot/title/menu/unbound). */
export function sceneIds() {
  return jsonlRows("extracted/data/scenes/scenes.jsonl").map((r) => r.scene_id);
}

/** The 20 story-scene spawn placements (the only projecting cell today). */
export function storySpawns() {
  return jsonlRows("extracted/data/scenes/scenes.jsonl")
    .filter((r) => r.spawn)
    .map((r) => ({ scene_id: r.scene_id, ...r.spawn }));
}

/* ------------------------------------------------------------------ */
/* AC MV-0.4 — two-list family ledger law                              */
/* ------------------------------------------------------------------ */

const DISPOSITIONS = new Set(["emitted", "deferred"]);

/**
 * Full ledger law over one {pending_families, placement_families} object.
 * Returns a list of violation strings ([] == lawful).
 * - opts.eligibleTotal: number (fresh recount)
 * - opts.tally: Map "kind|class" -> count (fresh recount; drives coverage +
 *   disjointness at count granularity: summing poi_rows per (kind,class)
 *   across families must reproduce the pool exactly)
 * - opts.declaredMarkerRowCount: number (data-row count of markers file)
 */
export function checkLedgerLaw(ledger, opts) {
  const v = [];
  const pending = ledger.pending_families ?? [];
  const placement = ledger.placement_families ?? [];

  // structural: closed axes, vocabulary, field presence
  for (const f of pending) {
    if (!f.family_id) v.push(`pending family without family_id: ${JSON.stringify(f).slice(0, 80)}`);
    // A-MV1 F-1: no entry may key a bare kind — every entry closes a class list
    if (!Array.isArray(f.poi_classes) || f.poi_classes.length === 0)
      v.push(`${f.family_id}: bare-kind key (poi_classes empty)`);
    if (!Array.isArray(f.poi_kinds) || f.poi_kinds.length === 0)
      v.push(`${f.family_id}: poi_kinds empty`);
    if (typeof f.poi_rows !== "number")
      v.push(`${f.family_id}: poi_rows missing/not a number`);
    if (!DISPOSITIONS.has(f.disposition))
      v.push(`${f.family_id}: disposition "${f.disposition}" is not emitted|deferred (no third state)`);
    if (f.emitted_markers !== undefined && !Number.isInteger(f.emitted_markers))
      v.push(`${f.family_id}: emitted_markers not an integer`);
  }
  for (const f of placement) {
    if (!f.family_id) v.push(`placement family without family_id`);
    if (!f.source_dataset) v.push(`${f.family_id}: placement family missing source_dataset`);
    if ("poi_rows" in f || "poi_classes" in f)
      v.push(`${f.family_id}: placement families carry neither poi_rows nor poi_classes`);
    if (!DISPOSITIONS.has(f.disposition))
      v.push(`${f.family_id}: disposition "${f.disposition}" is not emitted|deferred`);
  }

  // (a) partition sum
  const sum = pending.reduce((a, f) => a + (f.poi_rows ?? 0), 0);
  if (sum !== opts.eligibleTotal)
    v.push(`(a) Σ poi_rows=${sum} != eligible recount ${opts.eligibleTotal}`);

  // (b) coverage + disjointness. poi-kinds.json rules ONE kind per class, so
  // classes are compared by name. Three laws:
  //   b1 — a class claimed by >1 family is legal ONLY as container-scoped
  //        siblings (every claimer declares level_scope); bare double-claims
  //        fail outright ("no row in two families");
  //   b2 — every family's poi_rows equals what the fresh pool implies for its
  //        closed axis (scope-aware: include/exclude levels), so over-claims,
  //        under-claims and stale counts all fail;
  //   b3 — every eligible class is claimed by ≥1 family.
  const claimers = new Map(); // class -> families[]
  for (const f of pending) {
    for (const c of f.poi_classes ?? []) {
      const list = claimers.get(c) ?? [];
      list.push(f);
      claimers.set(c, list);
    }
  }
  for (const [cls, fams] of claimers) {
    if (fams.length > 1 && fams.some((f) => !f.level_scope))
      v.push(`(b1) ${cls}: claimed by ${fams.length} families but not all declare container scopes (row double-claim)`);
  }
  const poolLevels = opts.levels ?? new Map();
  for (const f of pending) {
    let expected = 0;
    for (const c of f.poi_classes ?? []) {
      for (const [key, n] of opts.tally.entries()) {
        if (!key.endsWith(`|${c}`) || !f.poi_kinds.includes(key.split("|")[0])) continue;
        const byLvl = poolLevels.get(c);
        if (f.level_scope?.include)
          for (const lvl of f.level_scope.include) expected += byLvl?.get(lvl) ?? 0;
        else if (f.level_scope?.exclude) {
          const excl = new Set(f.level_scope.exclude);
          for (const [lvl, nLvl] of byLvl ?? []) if (!excl.has(lvl)) expected += nLvl;
        } else expected += n;
      }
    }
    if ((f.poi_rows ?? 0) !== expected)
      v.push(`(b2) ${f.family_id}: claims ${f.poi_rows} rows, the fresh pool implies ${expected}`);
  }
  for (const [key] of opts.tally.entries()) {
    const cls = key.split("|")[1];
    if (!claimers.has(cls)) v.push(`(b3) ${cls}: eligible rows claimed by NO family`);
  }
  for (const [cls] of claimers) {
    if (![...opts.tally.keys()].some((k) => k.endsWith(`|${cls}`)))
      v.push(`(b2) ${cls}: family claims rows the eligible pool does not have`);
  }

  // (c) emitted total over BOTH lists equals markers data-row count
  const emitted =
    [...pending, ...placement].reduce((a, f) => a + (f.emitted_markers ?? 0), 0);
  if (emitted !== opts.declaredMarkerRowCount)
    v.push(`(c) Σ emitted_markers=${emitted} != markers data-row count ${opts.declaredMarkerRowCount}`);

  // (d) deferred accountability
  for (const f of [...pending, ...placement]) {
    if (f.disposition === "deferred") {
      if (!f.reason_code || typeof f.reason_code !== "string")
        v.push(`(d) ${f.family_id}: deferred without reason_code`);
      if (!f.unblock_owner || typeof f.unblock_owner !== "string")
        v.push(`(d) ${f.family_id}: deferred without unblock_owner`);
    }
  }
  return v;
}

/**
 * Row-granular disjointness/coverage over a concrete pool: which families
 * claim `row` = {kind, class, level}? Lawful pools yield EXACTLY ONE family
 * per row (the container-scoped minigame siblings partition level1 vs the
 * rest). Used on fixtures to prove "each eligible row claimed by exactly one
 * family" beyond count arithmetic.
 */
export function assignRowToFamilies(row, families) {
  const hits = [];
  for (const f of families) {
    if (!f.poi_kinds.includes(row.kind)) continue;
    if (!f.poi_classes.includes(row.class)) continue;
    const scope = f.level_scope;
    if (scope) {
      if (scope.include && !scope.include.includes(row.level)) continue;
      if (scope.exclude && scope.exclude.includes(row.level)) continue;
    }
    hits.push(f.family_id);
  }
  return hits;
}

/* ------------------------------------------------------------------ */
/* AC MV-0.3 / §3.2(b) — marker row shape matrix                       */
/* ------------------------------------------------------------------ */

const POSITION_STATUS = new Set(["projected", "awaiting-transform-stage", "scene-granular"]);

/**
 * Validate one marker row against §4.1 + §3.2(b). Returns violation strings.
 * ctx.routedSegments: entity_kind -> URL segment (routes.ts KIND_SEGMENT).
 * ctx.ownerIds: {cartridges,profiles,minigames} Sets for the join audit.
 * ctx.hostedMinigames: Map container -> Set(minigame ids) for the
 * instance_census requirement (>1 host ⇒ census mandatory, never one-of-N).
 */
export function validateMarkerRow(row, ctx) {
  const v = [];
  const req = (ok, msg) => { if (!ok) v.push(msg); };
  req(typeof row.marker_id === "string" && row.marker_id.length > 0, `${label(row)}: marker_id required`);
  req(typeof row.layer === "string", `${label(row)}: layer required`);
  req(typeof row.kind === "string", `${label(row)}: kind required`);
  req(typeof row.entity_kind === "string", `${label(row)}: entity_kind required`);
  req(typeof row.entity_slug === "string" && row.entity_slug.length > 0, `${label(row)}: entity_slug required`);
  req(
    row.icon && typeof row.icon.fallback_state === "string",
    `${label(row)}: icon.fallback_state required (explicit-missing rendering)`
  );
  req(row.position && POSITION_STATUS.has(row.position.status),
    `${label(row)}: position.status must be projected|awaiting-transform-stage|scene-granular`);
  req(Boolean(row.placement) && typeof row.placement.mechanism === "string"
    && typeof row.placement.source_join === "string",
    `${label(row)}: placement {mechanism,source_join} provenance required`);
  req(Boolean(row.links) && typeof row.links.page_url === "string" && typeof row.links.focus_url === "string",
    `${label(row)}: links.{page_url,focus_url} required`);

  const placementSourced = row.placement_source != null;
  if (placementSourced) {
    req(["DS-5", "minigame--scene-carrier"].includes(row.placement_source),
      `${label(row)}: unknown placement_source "${row.placement_source}"`);
    // A-MV1 OQ-7/F-2: poi_id null MANDATORY; scene-granularity always
    req(row.poi_id === null, `${label(row)}: placement-sourced row must carry poi_id:null`);
    req(row.position?.status === "scene-granular",
      `${label(row)}: placement-sourced row must be scene-granular, got "${row.position?.status}"`);
    // emitter-split scalar container; downstream compound-id splitting is a
    // forbidden derivation (§3.2(b), §4 defect class)
    req(typeof row.container === "string" && row.container.length > 0,
      `${label(row)}: scalar container field required`);
    req(!(/[,@]/.test(row.container ?? "")),
      `${label(row)}: container "${row.container}" is still a compound id`);
    req(row.instance_census && Number.isInteger(row.instance_census.total) && row.instance_census.total >= 1,
      `${label(row)}: instance_census.total required`);
    // never a plotted pin, never finer than class×container co-presence
    if (row.placement_source === "minigame--scene-carrier") {
      const hosted = ctx.hostedMinigames?.get(row.container);
      if (hosted && hosted.size > 1)
        req(Number.isInteger(row.instance_census?.minigames_hosted) && row.instance_census.minigames_hosted >= hosted.size,
          `${label(row)}: container hosts ${hosted.size} minigames — instance_census.minigames_hosted must not be silently one-of-N`);
    }
  } else {
    req(typeof row.poi_id === "string" && row.poi_id.length > 0,
      `${label(row)}: poi-pool row requires a corpus-verbatim poi_id anchor`);
  }

  // join audit (AC MV-0.1): slug resolves to exactly one owning-dataset id
  const set = ctx.ownerIds?.[row.entity_kind];
  if (set && !set.has(row.entity_slug))
    v.push(`${label(row)}: join audit FAIL — entity_slug "${row.entity_slug}" is not an owning-dataset id (${row.entity_kind})`);

  // routed segment agreement (§4.1 namespace split)
  const seg = ctx.routedSegments?.[row.entity_kind];
  if (seg && typeof row.links?.page_url === "string")
    req(row.links.page_url.startsWith(`/${seg}/${row.entity_slug}`),
      `${label(row)}: page_url "${row.links.page_url}" does not start with /${seg}/${row.entity_slug}`);
  if (typeof row.links?.focus_url === "string") {
    req(row.links.focus_url.startsWith("/map?focus="),
      `${label(row)}: focus_url must target /map?focus=`);
    req(row.links.focus_url.includes(`focus=${row.entity_kind}%3A${row.entity_slug}`) ||
        row.links.focus_url.includes(`focus=${row.entity_kind}:${row.entity_slug}`),
      `${label(row)}: focus_url does not carry ${row.entity_kind}:${row.entity_slug}`);
  }
  return v;
}

function label(row) {
  return row.marker_id ?? JSON.stringify(row).slice(0, 60);
}

/* ------------------------------------------------------------------ */
/* AC MV-2 — status/projection agreement                               */
/* ------------------------------------------------------------------ */

/**
 * MV-2 both directions: status:"projected" ⇔ the projection yields numbers.
 * Rows carrying explicit source/space go through projectedCoordinates()
 * directly; plain §4.1 rows (no source/space — the emitted v2 shape) go
 * through the projection module's markerStatusDisagrees() bridge, which is
 * the same conjunction with the emitter's inline∧world-assumed claim.
 */
export function agreementViolations(row) {
  const v = [];
  const pos = row.position ?? {};
  const hasAxis = (pos.source ?? row.source) != null || (pos.space ?? row.space) != null;
  if (hasAxis) {
    const input = {
      source: pos.source ?? row.source,
      space: pos.space ?? row.space,
      x: pos.x ?? row.x,
      y: pos.y ?? row.y,
      z: pos.z ?? row.z,
    };
    const coords = projectedCoordinates(input);
    const claimsProjected = pos.status === "projected";
    if (claimsProjected && coords === null)
      v.push(`${label(row)}: claims status "projected" but projectedCoordinates() refuses its floats`);
    if (!claimsProjected && coords !== null)
      v.push(`${label(row)}: projects to ${JSON.stringify(coords)} but status is "${pos.status}" (inverse disagreement)`);
  } else {
    if (markerStatusDisagrees({ status: pos.status, x: pos.x, y: pos.y, z: pos.z }))
      v.push(`${label(row)}: emitted status "${pos.status}" disagrees with the projection bridge (MV-2)`);
  }
  return v;
}

/* ------------------------------------------------------------------ */
/* Discovery helper for v2 exports the CodeWriter owns                 */
/* ------------------------------------------------------------------ */

/**
 * Find the first present export among `candidates`. Throws a guidance error
 * listing every accepted name when none exists (RED with instructions, never
 * a crash of unrelated tests).
 */
export function findExport(ns, candidates, usage) {
  const found = findExportSoft(ns, candidates);
  if (found) return found;
  throw new Error(
    `TW-MV1 contract gap: none of the exports [${candidates.join(", ")}] found.\n` +
    `The map-viewer suite pins this contract: ${usage}\n` +
    `Implement one of these names (or agree a rename with the orchestrator) — the test name tells you which AC is blocked.`
  );
}

/** Non-throwing variant: null when absent (for try-alternative-modules probes). */
export function findExportSoft(ns, candidates) {
  for (const name of candidates ?? []) {
    if (ns && typeof ns[name] === "function") return { name, fn: ns[name] };
  }
  return null;
}
