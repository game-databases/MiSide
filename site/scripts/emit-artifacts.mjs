/*
 * Build step (AC S11): emits the machine plane into public/ —
 *   • static JSON API  public/api/v1/<kind>/<id>.json (+ index per kind)
 *     URL-derivable from the page URL; fact-identical fields to what pages render
 *   • search indexes   public/search/<locale>.idx.json  (×34, disposable derived artifacts)
 *   • map registry     public/map/registry.json + public/map/markers.json
 *   • llms.txt         public/llms.txt
 *
 * Self-contained on purpose (no TS import): reads the SAME contract files and
 * resolves the SAME pointers as src/data/*; both sides are pinned to the
 * contract documents so they cannot drift silently.
 *
 * Run: node scripts/emit-artifacts.mjs   (wired as prebuild)
 */
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const extracted =
  process.env.MISIDE_EXTRACTED_ROOT ?? join(root, "..", "extracted");
const pub = join(root, "public");

/* ---------- locale table (mirror of src/i18n/locales.ts — parity-tested) */
const LOCALES = [
  ["en", "English", ""],
  ["ru", "Russian", "/ru"],
  ["uk", "Ukrainian", "/uk"],
  ["be", "Belarusian", "/be"],
  ["bg", "Bulgarian", "/bg"],
  ["zh-Hans", "ChineseSimplified", "/zh-Hans"],
  ["zh-Hant", "ChineseTraditional", "/zh-Hant"],
  ["hr", "Croatian", "/hr"],
  ["cs", "Czech", "/cs"],
  ["fil", "Filipino", "/fil"],
  ["fr", "French", "/fr"],
  ["de", "German", "/de"],
  ["hu", "Hungarian", "/hu"],
  ["id", "Indonesia", "/id"],
  ["it", "Italian", "/it"],
  ["ja", "Japanese", "/ja"],
  ["kk", "Kazakh", "/kk"],
  ["ko", "Korean", "/ko"],
  ["fa", "Persian", "/fa"],
  ["pl", "Polish", "/pl"],
  ["pt-PT", "Portugues Portugal", "/pt-PT"],
  ["pt-BR", "Português-Brasil", "/pt-BR"],
  ["ro", "Romanian", "/ro"],
  ["sr-Latn", "Serbian (Latin)", "/sr-Latn"],
  ["sk", "Slovak", "/sk"],
  ["es-419", "Spanish (LatinAmerica)", "/es-419"],
  ["es-ES", "Spanish (Spain)", "/es-ES"],
  ["sv", "Swedish", "/sv"],
  ["th", "Thai", "/th"],
  ["tr", "Turkish", "/tr"],
  ["vi", "Vietnamese", "/vi"],
  ["ar", "Arabic", "/ar"],
  ["ar-EG", "Arabic (Egyptian)", "/ar-EG"],
  ["ru-x-prerev", "Pre-revolutionaryRussian", "/ru-x-prerev"],
];

/* ---------- jsonl helpers ---------- */
function looksLikeHeader(obj, idField) {
  if (!obj || typeof obj !== "object") return false;
  const keys = Object.keys(obj);
  if (keys.includes("_meta")) return true;
  return (
    ["derived_fields", "schema", "schema_id", "generator"].some((k) =>
      keys.includes(k)
    ) && (!idField || !keys.includes(idField))
  );
}

// Two corpus header shapes (wrapped _meta vs documents-family bare header);
// empty-by-contract files tolerated. Must mirror src/data/contracts.ts.
function readJsonl(rel, idField) {
  let raw;
  try {
    raw = readFileSync(join(extracted, rel), "utf8");
  } catch (err) {
    if (err.code === "ENOENT") return { meta: null, rows: [] };
    throw err;
  }
  const lines = raw.split("\n").filter((l) => l.trim());
  if (lines.length === 0) return { meta: null, rows: [] };
  let meta = null;
  let start = 0;
  const first = JSON.parse(lines[0]);
  if (looksLikeHeader(first, idField)) {
    meta = first._meta !== undefined ? first._meta : first;
    start = 1;
  }
  const rows = lines.slice(start).map((l) => JSON.parse(l));
  if (meta && typeof meta.row_count === "number" && meta.row_count !== rows.length) {
    throw new Error(`${rel}: _meta.row_count ${meta.row_count} != ${rows.length}`);
  }
  return { meta, rows };
}

const locCache = new Map();
function locLines(dirName, category) {
  const key = `${dirName} ${category}`;
  if (locCache.has(key)) return locCache.get(key);
  const file = join(extracted, "localization", dirName, `${category}.jsonl`);
  const lines = [];
  if (existsSync(file)) {
    for (const line of readFileSync(file, "utf8").split("\n")) {
      if (!line.trim()) continue;
      const rec = JSON.parse(line);
      lines[rec.line_index] = rec.text ?? "";
    }
  }
  locCache.set(key, lines);
  return lines;
}
/** ARITHMETIC-FREE resolution (AC S13): pointers already carry emitted offsets. */
function resolveLoc(dirName, pointer) {
  if (!pointer) return "";
  const v = locLines(dirName, pointer.category)[pointer.line_index];
  return typeof v === "string" ? v : "";
}

function paletteHex(rgba) {
  const ch = (f) =>
    Math.min(255, Math.max(0, Math.round(f * 255))).toString(16).padStart(2, "0");
  return `#${ch(rgba[0])}${ch(rgba[1])}${ch(rgba[2])}`;
}

// VC-2 fix #1: honest de-slug for ids the client never names — separators
// become spaces, letter↔digit and camelCase boundaries split, words
// title-cased ("mta"→"Mta", "Books0"→"Books 0"). Re-spaces shipped strings;
// never composes a lore name. Mirrors desluggedLabel() in entityView.tsx.
function deslug(raw) {
  return raw
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([a-zA-Z])(\d)/g, "$1 $2")
    .replace(/(\d)([a-zA-Z])/g, "$1 $2")
    .replace(/[-_.]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/* ---------- kinds ---------- */
// [apiKind, file, idField, segment, filter?, titleFn(row, dirName)]
const KINDS = [
  ["mita", "data/characters/personages.jsonl", "character_id", "mita",
    (r) => r.kind === "mita",
    (r, dir) => resolveLoc(dir, r.name_loc)],
  ["players", "data/characters/personages.jsonl", "character_id", "players",
    (r) => r.kind === "player",
    (r, dir) => resolveLoc(dir, r.name_loc)],
  ["cartridges", "data/cartridges/cartridges.jsonl", "cartridge_id", "cartridges",
    null,
    // VC-2 fix #1: label rides the PINNED joins only — depicts (character) /
    // contains (player) resolve to the registry's own human labels; a row
    // with neither anchor (`mta`, DS-4 namespace honesty) keeps its save_key
    // re-spaced. Mirrors displayName() in entityView.tsx.
    (r, dir) => {
      const via = r.depicts_character_id ?? r.contains_player_id;
      if (via) {
        const dep = characterNameById.get(via);
        if (dep) {
          const named = resolveLoc(dir, dep);
          if (named) return named;
        }
      }
      return deslug(r.save_key) || r.save_key;
    }],
  ["minigames", "data/cartridges/minigames.jsonl", "minigame_id", "minigames",
    null,
    (r, dir) => (r.name_loc ? resolveLoc(dir, r.name_loc) : "") || deslug(r.client_key) || r.client_key],
  ["achievements", "data/achievements/achievements.jsonl", "achievement_id", "achievements",
    null,
    (r, dir, code) => r.display?.[code]?.name ?? r.achievement_id],
  ["endings", "data/endings/endings.jsonl", "ending_id", "endings",
    null,
    (r, dir) => (r.display_name_loc ? resolveLoc(dir, r.display_name_loc) : "") || deslug(r.ending_id)],
  ["profiles", "data/documents/profile_documents.jsonl", "document_id", "lore/profiles",
    null,
    (r, dir) => resolveLoc(dir, r.name_loc)],
  ["lore", "data/documents/world_documents.jsonl", "document_id", "lore",
    (r) => ["paper_part", "novella_surface"].includes(r.family),
    (r) => deslug(r.document_id)],
  ["books", "data/documents/books.jsonl", "book_id", "lore/books",
    null,
    // No display-name column exists: the client's own texture basename
    // ("Book 1") IS the label — re-spaced so "Books0" reads "Books 0".
    (r) => {
      const base = r.texture_rel ? r.texture_rel.split("/").pop().replace(/\.(webp|png)$/i, "") : "";
      return (base && deslug(base)) || r.book_id;
    }],
  ["locations", "data/scenes/scenes.jsonl", "scene_id", "locations",
    null,
    // VC-1 fix #2: human titles — scenes ride their client chapter name;
    // nameless containers fall back to a re-spaced id on pages/API and are
    // kept OUT of the search index by the searchable predicate below.
    (r, dir) => (r.chapter_name_loc ? resolveLoc(dir, r.chapter_name_loc) : "") || deslug(r.scene_id),
    // boot/menu/title containers have no human name anywhere: not searchable
    (r) => Boolean(r.chapter_name_loc)],
];

function emitJson(rel, obj) {
  const file = join(pub, rel);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(obj), "utf8");
}

/* ---------- main ---------- */
// VC-1 fix #2: cartridges carry no display-name table, so their search text
// resolves through the DEPICTED CHARACTER's name (personages name_loc).
const characterNameById = new Map(); // character_id -> name_loc pointer
for (const row of readJsonl("data/characters/personages.jsonl", "character_id").rows) {
  if (row.character_id) characterNameById.set(String(row.character_id), row.name_loc);
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

// VC-1 fix #2: per-locale row ACCUMULATOR — each kind appends; the file is
// written once after the loop. (Writing inside the kind loop made every kind
// overwrite the previous one, so only locations survived in the index.)
const searchByLocale = new Map(); // code -> SearchRow[]
for (const [code] of LOCALES) searchByLocale.set(code, []);

let entityCount = 0;
for (const [apiKind, file, idField, segment, filter, titleFn, searchable] of KINDS) {
  let { rows } = readJsonl(file, idField);
  if (filter) rows = rows.filter(filter);

  // static JSON API — mirrors page facts (id/kind/name/build/url)
  mkdirSync(join(pub, "api", "v1", apiKind), { recursive: true });
  const indexRows = [];
  for (const row of rows) {
    const id = String(row[idField]);
    const record = {
      id,
      kind: apiKind,
      name_en: apiKind === "achievements" || apiKind === "endings"
        ? titleFn(row, "English", "en")
        : titleFn(row, "English"),
      build_id: row.build_id ?? BUILD_ID,
      version_label: row.version_label ?? VERSION_LABEL,
      url: `/${segment}/${id}`,
    };
    emitJson(join("api", "v1", apiKind, `${id}.json`), record);
    indexRows.push(record);
    entityCount++;
  }
  emitJson(join("api", "v1", `${apiKind}.json`), {
    kind: apiKind,
    count: indexRows.length,
    build_id: BUILD_ID,
    items: indexRows,
  });

  // search rows ×34 — resolved per-locale strings, never EN passthrough.
  // A row whose title resolves empty in a locale is omitted THERE (the
  // declared omission half of the filler policy): the index holds named
  // entities, never raw ids dressed as titles.
  for (const [code, dirName, prefix] of LOCALES) {
    const acc = searchByLocale.get(code);
    for (const row of rows) {
      const id = String(row[idField]);
      const title = titleFn(row, dirName, code);
      if (!title) continue;
      if (searchable && !searchable(row)) continue;
      let text = "";
      if (row.description_loc) text = resolveLoc(dirName, row.description_loc);
      else if (row.lore_loc) text = resolveLoc(dirName, row.lore_loc);
      // cartridges carry no client display-name table (cartridges contract
      // DS-4 rule 2: the save_key IS the label) — the depicted character's
      // name is the honest human text that makes them findable.
      if (!text && row.depicts_character_id) {
        const dep = characterNameById.get(row.depicts_character_id);
        if (dep) text = resolveLoc(dirName, dep) || row.depicts_character_id;
      }
      acc.push({
        id,
        kind: segment,
        title,
        text,
        url: `${prefix}/${segment}/${id}`,
      });
    }
  }
}

/* ---------- dialogue containers — routed transcript views ---------- */
// /dialogue/<level> pages exist for every carrier level; titles ride the
// scene chapter names where the scenes dataset holds one (per locale).
const dialogueRowsSrc = readJsonl("data/dialogue/nodes.jsonl", "id").rows;
const dialogueLevelCounts = new Map();
for (const n of dialogueRowsSrc) {
  const lvl = String(n.id).split(":")[0];
  dialogueLevelCounts.set(lvl, (dialogueLevelCounts.get(lvl) ?? 0) + 1);
}
const sceneChapterLoc = new Map(); // level -> chapter_name_loc
for (const s of readJsonl("data/scenes/scenes.jsonl", "scene_id").rows) {
  if (s.chapter_name_loc) sceneChapterLoc.set(s.scene_id, s.chapter_name_loc);
}
for (const [code, dirName, prefix] of LOCALES) {
  const acc = searchByLocale.get(code);
  for (const [lvl, nodeCount] of [...dialogueLevelCounts].sort()) {
    const ch = sceneChapterLoc.get(lvl);
    // R-FVC1 minor #1: carriers the scenes dataset does not name stay OUT of
    // the search index — the same predicate locations use ("never raw ids
    // dressed as titles"). The /dialogue/<lvl> pages themselves still ship.
    if (!ch) continue;
    acc.push({
      // R-FVC1 minor #2: plain carrier id here — the final namespacing pass
      // below prepends the kind once ("dialogue:<lvl>"); pre-prefixing made
      // every dialogue row "dialogue:dialogue:<lvl>".
      id: lvl,
      kind: "dialogue",
      title: resolveLoc(dirName, ch),
      text: `nodes:${nodeCount}`,
      url: `${prefix}/dialogue/${lvl}`,
    });
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

/* ---------- search index files — written ONCE per locale after all appends ---------- */
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

/* ---------- map registry + markers ---------- */
const sceneRows = readJsonl("data/scenes/scenes.jsonl", "scene_id").rows;
emitJson(
  join("map", "registry.json"),
  sceneRows.map((s) => ({
    scene_id: s.scene_id,
    role: s.role,
    bounds: null, // settles at the P5/S9 calibration rerun
    zoom: [1, 4],
    "coordinate-transform": "rect-per-map",
    imagery: "authored",
    status: "awaiting-artwork",
    build_id: s.build_id,
  }))
);
const markerFile = readJsonl("data/scenes/markers.jsonl", "entity_kind");
// v0 is _meta-only by contract (no-orphan rule); emit whatever data rows exist
emitJson(join("map", "markers.json"), {
  _meta: markerFile.meta,
  rows: markerFile.rows,
});

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

## Pages

Entity pages exist at bare paths (English) and under each locale prefix:
/${"{locale}"}/{kind}/{id}. The site has no search route; the header field
answers in place.

## What this database does not hold

No invented values: fields the client does not prove are absent or marked
pending. Audio, video and 3D assets are catalogued, never served.
`,
  "utf8"
);

console.log(
  `emit-artifacts: ${entityCount} entity records, ${
    KINDS.length
  } kind indexes, ${LOCALES.length} search indexes, map registry ${
    sceneRows.length
  } scenes, markers ${markerFile.rows.length}, build ${BUILD_ID}`
);
