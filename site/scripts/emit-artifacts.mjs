/*
 * Build step (AC S11): emits the machine plane into public/ —
 *   • static JSON API  public/api/v1/<kind>/<id>.json (+ index per kind)
 *     URL-derivable from the page URL; fact-identical fields to what pages render
 *   • search indexes   public/search/<locale>.idx.json  (×34, disposable derived artifacts)
 *   • map registry     public/map/registry.json + public/map/markers.json
 *   • llms.txt         public/llms.txt
 *
 * B-RP1 RE-PIN: the private KINDS table, per-kind title functions, de-slug
 * helper and per-locale row assembly that lived here were a SECOND copy of
 * the contract readers — free to drift from what pages serve. This script now
 * imports THE reader layer itself (src/data/contracts.ts +
 * src/components/routes/entityDisplay.ts + src/lib/search/searchSource.ts,
 * executed by Node's native type stripping), so emitted artifacts are built
 * from exactly the shapes the site serves, and the pivot census is
 * reconciled against contracts/registry/entities.json at emit time
 * (assertSearchCensus).
 *
 * Run: node scripts/emit-artifacts.mjs   (wired as prebuild)
 */
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ENTITY_KINDS, kindRows, readJsonl } from "../src/data/contracts.ts";
import { displayName } from "../src/components/routes/entityDisplay.ts";
import { KIND_SEGMENT } from "../src/lib/routes.ts";
import { LOCALES } from "../src/i18n/locales.ts";
import {
  buildAllLocaleSearchRows,
  assertSearchCensus,
} from "../src/lib/search/searchSource.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const extracted =
  process.env.MISIDE_EXTRACTED_ROOT ?? join(root, "..", "extracted");
const pub = join(root, "public");
void extracted; // readers resolve the corpus root themselves (jsonl.ts)

function emitJson(rel, obj) {
  const file = join(pub, rel);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(obj), "utf8");
}

import { emitContent } from "./build-content.mjs";

/* ---------- main ---------- */
// Content pipeline (M2): compile authored articles BEFORE any consumer reads
// the registry — search rows, static API and llms.txt all join it below.
const contentResult = emitContent();
if (!contentResult.ok) {
  throw new Error(`build-content failed with ${contentResult.errors?.length ?? "?"} error(s)`);
}

const scenesMeta = readJsonl("data/scenes/scenes.jsonl", "scene_id").meta;
const buildIdPins = scenesMeta?.build_pins ?? {};
const BUILD_ID =
  process.env.MISIDE_BUILD_ID ??
  buildIdPins.buildId ??
  buildIdPins.build_id ??
  String(scenesMeta?.build_id ?? "19029065");
const VERSION_LABEL = buildIdPins.versionLabel ?? "0.93L";

for (const locale of LOCALES) mkdirSync(join(pub, "search"), { recursive: true });

let entityCount = 0;
// Routed kinds drive BOTH emissions — ENTITY_KINDS is the single kind table
// (AC S6: generateStaticParams == owning contract id column).
for (const [kind, def] of Object.entries(ENTITY_KINDS)) {
  const segment = KIND_SEGMENT[kind];
  if (!segment) throw new Error(`routed kind without URL segment: ${kind}`);
  const rows = kindRows(kind);

  // static JSON API — mirrors page facts (id/kind/name/build/url); names ride
  // the SAME display-name layer the pages use, EN pivot only (glue register)
  mkdirSync(join(pub, "api", "v1", kind), { recursive: true });
  const indexRows = [];
  for (const row of rows) {
    const id = String(row[def.idField]);
    const record = {
      id,
      kind,
      name_en: displayName(kind, row, "en"),
      build_id: row.build_id ?? BUILD_ID,
      version_label: row.version_label ?? VERSION_LABEL,
      url: `/${segment}/${id}`,
    };
    emitJson(join("api", "v1", kind, `${id}.json`), record);
    indexRows.push(record);
    entityCount++;
  }
  emitJson(join("api", "v1", `${kind}.json`), {
    kind,
    count: indexRows.length,
    build_id: BUILD_ID,
    items: indexRows,
  });
}

// Search rows ×34 — built ONCE by the shared reader-side builder
// (availability-gated, filler-policy omissions included), reconciled against
// entities.json, then written per locale.
const searchByLocale = buildAllLocaleSearchRows();
assertSearchCensus(searchByLocale);

// Article rows join the SAME per-locale indexes (spec §3.2): one row per
// published article × its ADMITTED locale cells; the namespacing pass below
// yields the law's "guides:<slug>" / "news:<slug>" document ids.
let articleRowCount = 0;
for (const row of contentResult.registryRows) {
  const kind = row.type === "guide" ? "guides" : "news";
  for (const [code, cell] of Object.entries(row.locales)) {
    const acc = searchByLocale.get(code);
    if (!acc) continue;
    acc.push({ id: row.slug, kind, title: cell.title, text: cell.description, url: cell.path });
    articleRowCount++;
  }
}

// Search-index integrity pin: MiniSearch.addAll throws on any duplicate id,
// which takes out the ENTIRE per-locale index client-side. Fail the build
// here instead of shipping a silently dead search. Keyed on the KIND-
// NAMESPACED form — raw columns legitimately repeat across kinds ("level4"
// is both a scene_id and a dialogue carrier); only the final document id
// must be unique.
for (const [code, rows] of searchByLocale) {
  const seen = new Set();
  for (const r of rows) {
    const key = `${r.kind}:${r.id}`;
    if (seen.has(key)) throw new Error(`${code}.idx.json: duplicate id ${key}`);
    seen.add(key);
  }
}

/* ---------- search index files — written ONCE per locale ---------- */
// Document ids are kind-namespaced: MiniSearch requires globally-unique ids
// and separate kinds DO collide on the raw column (a scene_id and a dialogue
// carrier level are both "level4"). A duplicate id makes addAll throw, which
// kills every browser-side query — not just the colliding rows.
for (const [code, rows] of searchByLocale) {
  const seen = new Set();
  const namespaced = rows.map((r) => {
    const id = `${r.kind}:${r.id}`;
    if (seen.has(id)) throw new Error(`search index (${code}): duplicate id ${id}`);
    seen.add(id);
    return { ...r, id };
  });
  emitJson(join("search", `${code}.idx.json`), namespaced);
}

/* ---------- map registry v2 + markers (map-viewer §3.2(d); additive over v1) ---------- */
const sceneRows = readJsonl("data/scenes/scenes.jsonl", "scene_id").rows;
const markerFile = readJsonl("data/scenes/markers.jsonl", "entity_kind");
// Per-scene per-kind marker counts. Scene attribution mirrors the site's
// markerSceneId() law (placement.scene_binding first, else the poi anchor).
const perKindByScene = {};
for (const m of markerFile.rows) {
  const scene = m.placement?.scene_binding ?? String(m.poi_id ?? "").split(":")[0];
  if (!scene) continue;
  (perKindByScene[scene] ??= {});
  perKindByScene[scene][m.kind] = (perKindByScene[scene][m.kind] ?? 0) + 1;
}
emitJson(
  join("map", "registry.json"),
  sceneRows.map((s) => ({
    scene_id: s.scene_id,
    role: s.role,
    // chapter pointer or explicit null — never a guessed display label
    display_label_loc: s.chapter_name_loc ?? null,
    bounds: null, // settles at the P5/S9 calibration rerun
    zoom: [1, 4],
    "coordinate-transform": "rect-per-map",
    imagery: "authored",
    status: existsSync(join(pub, "map", s.scene_id, "base.svg"))
      ? "ready"
      : "awaiting-artwork",
    per_kind: perKindByScene[s.scene_id] ?? {},
    build_id: s.build_id,
  }))
);
// emit whatever data rows exist (zero by contract until the M0 rerun lands)
emitJson(join("map", "markers.json"), {
  _meta: markerFile.meta,
  rows: markerFile.rows,
});

/* ---------- article static JSON API (AC S11 law extends to articles) ----- */
for (const section of ["guides", "news"]) {
  const rows = contentResult.registryRows.filter((r) =>
    section === "guides" ? r.type === "guide" : r.type !== "guide"
  );
  mkdirSync(join(pub, "api", "v1", section), { recursive: true });
  const indexItems = [];
  for (const r of rows) {
    const record = {
      id: r.slug,
      type: r.type,
      slug: r.slug,
      title_en: r.title_en,
      locales: Object.fromEntries(
        Object.entries(r.locales).map(([code, c]) => [
          code,
          { path: c.path, title: c.title, description: c.description, word_count: c.word_count },
        ])
      ),
      spoiler: r.spoiler,
      verified_build_id: r.verified_build_id,
      published_at: r.published_at,
      updated_at: r.updated_at,
      url: r.locales.en ? r.locales.en.path : undefined,
      entities: r.entities,
    };
    emitJson(join("api", "v1", section, `${r.slug}.json`), record);
    indexItems.push({ id: r.slug, type: r.type, url: record.url, title_en: r.title_en });
  }
  emitJson(join("api", "v1", `${section}.json`), {
    section,
    count: indexItems.length,
    build_id: BUILD_ID,
    items: indexItems,
  });
}

/* ---------- llms.txt ---------- */
writeFileSync(
  join(pub, "llms.txt"),
  `# MiSide Database

Structured database of MiSide (AIHASTO; Steam appid 2527500), derived from a
full deconstruction of the game client. Every fact traces to extracted client
data; records carry the buildId of the extraction run.

## What the numbers mean

- buildId ${BUILD_ID} ("${VERSION_LABEL}") is the Steam client build this data
  was extracted from. All pages and API records carry it.
- Locale coverage follows the game's own localization files across all 34
  client locales. A category absent in a locale renders that locale's
  not-yet-translated state; a page is omitted only when an entity has zero
  strings there.

## JSON entry points

- Entity record: /api/v1/{kind}/{id}.json where the URL mirrors the page URL.
- Kind index: /api/v1/{kind}.json
- Kinds: mita, players, cartridges, minigames, achievements, endings,
  profiles, lore, books, locations.
- Search rows per locale: /search/{locale}.idx.json
- Map registry: /map/registry.json ; markers: /map/markers.json
- Articles: /api/v1/guides/{slug}.json and /api/v1/news/{slug}.json
  (indexes: /api/v1/guides.json, /api/v1/news.json)

## Pages

Entity pages exist at bare paths (English) and under each locale prefix:
/${"{locale}"}/{kind}/{id}. The site has no search route; the header field
answers in place.

Guides live at /guides/{slug} and news at /news/{slug} (bare English paths,
prefixed per translated locale). A translated page exists only where that
locale's own authored article exists — locales never mix languages.

## What this database does not hold

No invented values: fields the client does not prove are absent or marked
pending. Audio, video and 3D assets are catalogued, never served.
`,
  "utf8"
);

console.log(
  `emit-artifacts: ${entityCount} entity records, ${
    contentResult.registryRows.length
  } article records (${articleRowCount} article search rows), ${
    Object.keys(ENTITY_KINDS).length
  } kind indexes, ${LOCALES.length} search indexes, map registry ${
    sceneRows.length
  } scenes, markers ${markerFile.rows.length}, build ${BUILD_ID}`
);
