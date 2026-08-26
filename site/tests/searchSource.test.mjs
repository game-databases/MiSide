/*
 * B-RP1 — search-row builder law tests (LIVE corpus leg).
 *
 * The emitted public/search/<locale>.idx.json files must be built from the
 * SAME contract readers the pages serve — this file pins that construction
 * path directly:
 *   • census: per-kind pivot counts equal entities.json-derived expectations,
 *     computed INDEPENDENTLY here from contracts/registry/entities.json;
 *   • availability: every row's (locale, kind) passes the same ledger gate
 *     the routes notFound() on — a search row may never target a 404;
 *   • URL shape: prefix + routed segment + contract id column;
 *   • locale discipline: every locale's id-set ⊆ pivot's id-set and titles
 *     resolve per-locale (ru differs from en for the same entity);
 *   • dialogue transcript views stay chapter-named subsets of the carriers.
 * (The fixture leg proving reader-derivation lives in
 * searchSourceFixture.test.mjs — separate process, separate corpus root.)
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
process.env.MISIDE_EXTRACTED_ROOT ??= join(SITE_ROOT, "..", "extracted");

const { buildAllLocaleSearchRows, assertSearchCensus, SEARCH_KINDS } = await import(
  "../src/lib/search/searchSource.ts"
);
const { LOCALES, getLocale } = await import("../src/i18n/locales.ts");
const { kindAvailable } = await import("../src/data/availability.ts");
const { KIND_SEGMENT } = await import("../src/lib/routes.ts");
const KIND_SEGMENT_VALUES = new Set(Object.values(KIND_SEGMENT));

const entitiesRegistry = JSON.parse(
  readFileSync(join(SITE_ROOT, "..", "contracts", "registry", "entities.json"), "utf8")
).entity_types;

/** Independent double-entry expectations from the ACCEPTED registry (by URL segment). */
function expectedCensus() {
  const mitaEnum = entitiesRegistry.personage?.enums?.kind ?? {};
  const worldDoc = entitiesRegistry.world_document?.enums?.family ?? {};
  return {
    mita: { exact: mitaEnum.mita },
    players: { exact: mitaEnum.player },
    cartridges: { exact: entitiesRegistry.cartridge_item?.row_count },
    minigames: { exact: entitiesRegistry.minigame?.row_count },
    achievements: { exact: entitiesRegistry.achievement?.row_count },
    endings: { exact: entitiesRegistry.ending?.row_count },
    "lore/profiles": { exact: entitiesRegistry.profile_document?.row_count },
    "lore/books": { exact: entitiesRegistry.book?.row_count },
    lore: {
      exact: (worldDoc.paper_part ?? 0) + (worldDoc.novella_surface ?? 0),
    },
    locations: { max: entitiesRegistry.scene?.row_count },
    dialogue: { max: entitiesRegistry.dialogue_graph?.row_count },
  };
}

const allRows = buildAllLocaleSearchRows();
const PIVOT = LOCALES[0].code;

test("[B-RP1] the builder covers all 34 locales", () => {
  assert.equal(allRows.size, LOCALES.length);
  for (const l of LOCALES) assert.ok(allRows.has(l.code));
});

test("[B-RP1] pivot census reconciles with entities.json (independent derivation)", () => {
  const rows = allRows.get(PIVOT);
  const counts = new Map();
  for (const r of rows) counts.set(r.kind, (counts.get(r.kind) ?? 0) + 1);
  for (const [kind, want] of Object.entries(expectedCensus())) {
    const got = counts.get(kind) ?? 0;
    if (want.exact !== undefined) {
      assert.equal(got, want.exact, `kind ${kind} must equal the registry count`);
    }
    if (want.max !== undefined) {
      assert.ok(got <= want.max, `kind ${kind} stays within the registry bound`);
      assert.ok(got > 0, `kind ${kind} keeps its searchable subset`);
    }
  }
});

test("[B-RP1] assertSearchCensus accepts the built indexes", () => {
  assert.doesNotThrow(() => assertSearchCensus(allRows));
});

test("[B-RP1] every row rides the availability ledger the routes gate on", () => {
  for (const l of LOCALES) {
    for (const r of allRows.get(l.code)) {
      if (r.kind === "dialogue") continue; // transcript views admit all locales
      assert.equal(
        kindAvailable(l.code, r.kind),
        true,
        `row ${r.kind}:${r.id} in ${l.code} targets an unavailable page`
      );
    }
  }
});

test("[B-RP1] URL shape + facet vocabulary: kind IS the routed segment", () => {
  for (const r of allRows.get(PIVOT)) {
    // "dialogue" transcript views are their own routed tree, not a KIND_SEGMENT
    if (r.kind === "dialogue") {
      assert.match(r.url, /^\/dialogue\/[^/]+$/);
      continue;
    }
    assert.ok(KIND_SEGMENT_VALUES.has(r.kind), `kind ${r.kind} must be a routed segment`);
    assert.equal(r.url, `/${r.kind}/${r.id}`);
    assert.ok(r.title.length > 0, "no raw ids dressed as titles in the pivot index");
  }
  // the header's facet chips filter on r.kind verbatim — every facet kind
  // must therefore exist among the rows (VC-2: no dead facet)
  const have = new Set(allRows.get(PIVOT).map((r) => r.kind));
  for (const f of ["mita", "players", "cartridges", "minigames",
    "achievements", "endings", "lore/profiles", "lore/books",
    "locations", "dialogue"]) {
    assert.ok(have.has(f), `facet kind ${f} has no rows`);
  }
});

test("[B-RP1] locale discipline: subset ids + real per-locale resolution", () => {
  const pivotIds = new Set(allRows.get(PIVOT).map((r) => `${r.kind}:${r.id}`));
  for (const l of LOCALES) {
    if (l.code === PIVOT) continue;
    for (const r of allRows.get(l.code)) {
      assert.ok(
        pivotIds.has(`${r.kind}:${r.id}`),
        `${l.code} invented row ${r.kind}:${r.id}`
      );
      const def = getLocale(l.code);
      assert.ok(r.url.startsWith(def.prefix));
    }
  }
  // the same entity resolves DIFFERENT strings per locale (never EN passthrough)
  const enMita = allRows.get("en").find((r) => r.kind === "mita");
  const ruMita = allRows.get("ru").find((r) => r.kind === "mita" && r.id === enMita.id);
  assert.ok(enMita && ruMita);
  assert.notEqual(ruMita.title, enMita.title, "ru title must be the game's own Russian string");
});

test("[B-RP1] dialogue views are chapter-named subsets of the registry carriers", () => {
  const dlg = allRows.get(PIVOT).filter((r) => r.kind === "dialogue");
  const bound = expectedCensus().dialogue.max;
  assert.ok(dlg.length <= bound && dlg.length > 0);
  for (const r of dlg) assert.match(r.text, /^nodes:\d+$/);
});

test("[B-RP1] SEARCH_KINDS is exactly the routed kinds + dialogue", () => {
  assert.deepEqual([...SEARCH_KINDS], [
    "mita", "players", "cartridges", "minigames", "achievements",
    "endings", "profiles", "lore", "books", "locations", "dialogue",
  ]);
});
