/*
 * B-RP1 — relation-card law tests. Everything runs against SYNTHETIC
 * fixtures under temp MISIDE_EXTRACTED_ROOT + MISIDE_CONTRACTS_ROOT roots so
 * the assertions pin the CONSUMPTION LAWS, not today's corpus numbers:
 *   • registry-pinned family grouping (unregistered/META-ONLY → no card);
 *   • direction awareness — in-file mirror inverses collapse to one item ↔;
 *   • carry-law provenance inputs ride verbatim and bite off hard/moded;
 *   • fail-closed: null anchors, machine-plane forms and missing fields
 *     render as typed explicit states, never blanks/guesses;
 *   • no-orphan law: peers link only when the owning dataset confirms them;
 *   • density honesty: dense unlinked tokens collapse into counted rows;
 *   • consume-time census gate: disk drift from joins.json fails loud.
 * B-RP2 fix round adds: flat grant-site payload rendering on award-site cards,
 * method as carried provenance, ending peers linking through /endings, and the
 * search-census unknown-kind gate.
 * Env vars are set BEFORE any reader call (readers cache per process; node
 * --test gives this file its own process).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, readFileSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const root = mkdtempSync(join(tmpdir(), `relcards-${process.pid}`));
const extracted = join(root, "extracted");
const registry = join(root, "registry");
for (const d of [
  "data/characters",
  "data/cartridges",
  "data/minigames",
  "data/documents",
  "data/scenes",
  "data/endings",
  "relinks",
  "localization/English",
]) {
  mkdirSync(join(extracted, d), { recursive: true });
}
mkdirSync(registry, { recursive: true });

process.env.MISIDE_EXTRACTED_ROOT = extracted;
process.env.MISIDE_CONTRACTS_ROOT = registry;

/** jsonl with a wrapped _meta header (the WRAPPED corpus shape). */
function emitJsonl(rel, rows) {
  const file = join(extracted, rel);
  mkdirSync(join(file, ".."), { recursive: true });
  writeFileSync(
    file,
    [
      JSON.stringify({ _meta: { schema: "fixture", row_count: rows.length } }),
      ...rows.map((r) => JSON.stringify(r)),
    ].join("\n") + "\n"
  );
}

emitJsonl("data/characters/personages.jsonl", [
  { character_id: "mita-usual", kind: "mita", name_loc: { category: "Menu", line_index: 0 } },
]);
emitJsonl("data/cartridges/cartridges.jsonl", [
  { cartridge_id: "cart-mtashh", family: "character", save_key: "mtashh", depicts_character_id: "mita-usual" },
]);
emitJsonl("data/minigames/minigames.jsonl", [
  { minigame_id: "pinguin", client_key: "Pinguin" },
]);
emitJsonl("data/documents/world_documents.jsonl", [
  { document_id: "paperpart-level13-0", family: "paper_part" },
]);
emitJsonl("data/scenes/scenes.jsonl", [
  { scene_id: "level13", role: "story", chapter_name_loc: { category: "Menu", line_index: 1 } },
]);
writeFileSync(
  join(extracted, "localization", "English", "Menu.jsonl"),
  [
    JSON.stringify({ line_index: 0, text: "Usual Mita" }),
    JSON.stringify({ line_index: 1, text: "Level 13" }),
  ].join("\n") + "\n"
);
writeFileSync(
  join(extracted, "localization", "English", "Clothes.jsonl"),
  [JSON.stringify({ line_index: 12, text: "Christmas" })].join("\n") + "\n"
);

/* joins.json fixture — real family stems so the pinned PAGE_FAMILIES routing
   picks them up; counts are the fixture's own measured truth. */
const JOINS = {
  _meta: { build_pin: { build_id: "FIXTURE", version_label: "0.93L" }, expected_edge_total: 23 },
  families: {
    // split-bearing family with in-file mirrors + provenance variety
    "character--scene-membership": {
      binds: "character -> scene instances",
      file: "extracted/relinks/character--scene-membership.jsonl",
      schema_id: "fixture/1", anchor_mode: "endpoints",
      anchor_grammar: { from: ["<bare>", "scene:"], to: ["<bare>", "scene:", "scene-class:"] },
      direction_handling: "direction-split",
      edge_count_expected: 4, edge_count_measured: 4,
      mechanisms: { hard: 3, inferred: 1 }, statuses: { modeled: 3, partial: 1 },
    },
    // dense document→container family for the counted-rows collapse
    "document--scene-membership": {
      binds: "world_document -> scene",
      file: "extracted/relinks/document--scene-membership.jsonl",
      schema_id: "fixture/1", anchor_mode: "endpoints",
      anchor_grammar: { from: ["note:"], to: ["container:"] },
      direction_handling: "kind-encoded",
      edge_count_expected: 14, edge_count_measured: 14,
      mechanisms: { hard: 14 }, statuses: { modeled: 14 },
    },
    // outfit-unlock: unroutable outfit peers w/ display pointers + partials
    "minigame--outfit-unlock": {
      binds: "minigame -> ClothCompleted chain",
      file: "extracted/relinks/minigame--outfit-unlock.jsonl",
      schema_id: "fixture/1", anchor_mode: "endpoints",
      anchor_grammar: { from: ["minigame:", "outfit:"], to: ["minigame:", "outfit:"] },
      direction_handling: "direction-split",
      edge_count_expected: 2, edge_count_measured: 2,
      mechanisms: { hard: 1, logic: 1 }, statuses: { modeled: 1, partial: 1 },
    },
    // id-columns reverse index: scalar pair incl. an orphan achievement target
    "achievement--ending": {
      binds: "ending -> award achievement",
      file: "extracted/relinks/achievement--ending.jsonl",
      schema_id: "fixture/1", anchor_mode: "id-columns",
      direction_handling: "reverse-index",
      edge_count_expected: 2, edge_count_measured: 2,
      mechanisms: { hard: 2 }, statuses: {},
    },
    // id-columns provenance family: grant sites ship FLAT (level/file/method
    // + pathIDs) — exactly the corpus shape; row 1 is byte-equal to the real
    // extracted/relinks/achievement--award-site.jsonl ACHI_WinFIght row.
    "achievement--award-site": {
      binds: "achievement -> serialized grant sites",
      file: "extracted/relinks/achievement--award-site.jsonl",
      schema_id: "miside.relink.achievement-award-site/1", anchor_mode: "id-columns",
      direction_handling: "reverse-index",
      edge_count_expected: 2, edge_count_measured: 2,
      mechanisms: { hard: 2 }, statuses: {},
    },
    // provisional speaker themes: machine-plane peer w/ pending-curation status
    "dialogue-speaker-theme--character": {
      binds: "speaker theme -> character",
      file: "extracted/relinks/dialogue-speaker-theme--character.jsonl",
      schema_id: "fixture/1", anchor_mode: "endpoints",
      anchor_grammar: { from: ["speaker-theme:"], to: ["character:"] },
      direction_handling: "forward-only",
      edge_count_expected: 1, edge_count_measured: 1,
      mechanisms: { inferred: 1 }, statuses: { "provisional-pending-ds1": 1 },
    },
    // META-ONLY family: measured absence shipped as data → no card ever
    "cartridge--scene-placement": {
      binds: "cartridge -> pickup placement",
      file: "extracted/relinks/cartridge--scene-placement.jsonl",
      schema_id: "fixture/1", anchor_mode: "meta-only",
      direction_handling: "meta-only",
      edge_count_expected: 0, edge_count_measured: 0,
      mechanisms: {}, statuses: {},
    },
  },
};
writeFileSync(join(registry, "joins.json"), JSON.stringify(JOINS));

/* relink fixtures */
writeFileSync(
  join(extracted, "relinks", "character--scene-membership.jsonl"),
  [
    JSON.stringify({ direction: "forward", from: "mita-usual", to: "scene:level13", mechanism: "hard", status: "modeled" }),
    JSON.stringify({ direction: "inverse", from: "scene:level13", to: "mita-usual", mechanism: "hard", status: "modeled" }),
    JSON.stringify({ direction: "forward", from: "mita-usual", to: "scene-class:MitaPerson", instance_count: 93, mechanism: "inferred", status: "partial", missing_fields: ["reflection targets unproven - COMP J7"] }),
    JSON.stringify({ direction: "inverse", from: "scene:level13", to: "ghost-mita", mechanism: "logic", status: "partial" }),
  ].join("\n") + "\n"
);
{
  const rows = [];
  for (let i = 0; i < 14; i++) {
    rows.push(
      JSON.stringify({ kind: "forward", from: `note:note-level13-${i}`, to: "container:level13", mechanism: "hard", status: "modeled" })
    );
  }
  writeFileSync(join(extracted, "relinks", "document--scene-membership.jsonl"), rows.join("\n") + "\n");
}
writeFileSync(
  join(extracted, "relinks", "minigame--outfit-unlock.jsonl"),
  [
    JSON.stringify({ direction: "forward", from: "minigame:pinguin", to: "outfit:Chirfns", display_name_en: "Christmas", display_name_loc: { category: "Clothes", line_index: 12 }, mechanism: "hard", status: "modeled", missing_fields: [] }),
    JSON.stringify({ direction: "forward", from: "minigame:pinguin", to: "outfit:original", display_name_en: "Default", mechanism: "logic", status: "partial", missing_fields: ["reflection targets unproven"] }),
  ].join("\n") + "\n"
);
writeFileSync(
  join(extracted, "relinks", "achievement--ending.jsonl"),
  [
    JSON.stringify({ index_pair: "achievement->ending", achievement_id: "ACHI_real", ending_id: "conditions-met", mechanism: "hard" }),
    JSON.stringify({ index_pair: "achievement->ending", achievement_id: "ACHI_orphan", ending_id: "conditions-met", mechanism: "hard" }),
  ].join("\n") + "\n"
);
writeFileSync(
  join(extracted, "relinks", "dialogue-speaker-theme--character.jsonl"),
  [JSON.stringify({ direction: "forward", from: "speaker-theme:Mita", to: "character:mita-usual", mechanism: "inferred", status: "provisional-pending-ds1" })].join("\n") + "\n"
);
writeFileSync(
  join(extracted, "relinks", "achievement--award-site.jsonl"),
  [
    JSON.stringify({ index_pair: "achievement->award_site", achievement_id: "ACHI_WinFIght", level: "level6", file: "Dialogue_3DText_#7081.txt", host_object_path_id: 7081, target_type: "Achievement_function", target_path_id: 9330, method: "AchievementGet", args_string: "ACHI_WinFIght", mechanism: "hard", build_id: 19029065 }),
    // a row with NO grant-site payload keys — the typed named-absence path
    JSON.stringify({ index_pair: "achievement->award_site", achievement_id: "ACHI_bare", host_object_path_id: null, target_type: "Achievement_function", target_path_id: 42, method: "AchievementGet", args_string: "ACHI_bare", mechanism: "hard", build_id: 19029065 }),
  ].join("\n") + "\n"
);
emitJsonl("data/endings/endings.jsonl", [
  { ending_id: "conditions-met", kind: "ending", build_id: 19029065 },
]);
/* empty census registry: the search-census leg below pins the GUARD, not
   today's corpus numbers (the live corpus acceptance lives in the search lane) */
writeFileSync(
  join(registry, "entities.json"),
  JSON.stringify({ _meta: { note: "relationCards fixture leg: no census pins" }, entity_types: {} })
);

const { relationCardsFor, edgesAnchoringPage, provenanceBites, DENSE_TOKEN_LIMIT } = await import(
  "../src/lib/relations/relationCards.ts"
);

test("[B-RP1] location page: mirrored character edges collapse into one ↔ linked item", () => {
  const cards = relationCardsFor("locations", "level13", "en", "");
  const charCard = cards.find((c) => c.family === "character--scene-membership");
  assert.ok(charCard, "inbound characters card must exist on a location page");
  assert.equal(charCard.edgeCount, 4, "card carries the REGISTRY-measured family census");
  assert.equal(charCard.binds, "character -> scene instances");
  const usual = charCard.items.find((i) => i.label === "Usual Mita");
  assert.ok(usual, "the character peer renders with its own locale name");
  assert.equal(usual.state, "linked");
  assert.equal(usual.href, "/mita/mita-usual");
  assert.deepEqual(usual.directions.sort(), ["forward", "inverse"]);
  assert.equal(usual.arrow, "↔");
  // provenance rides VERBATIM in the VM; whether it RENDERS is the chip's
  // bite law (hard/modeled stays silent — pinned by provenanceBites below)
  assert.equal(usual.mechanism, "hard");
  assert.equal(usual.status, "modeled");
  const ghost = charCard.items.find((i) => i.key === "ghost-mita");
  assert.ok(ghost, "an unconfirmed peer still surfaces as an explicit state");
  assert.equal(ghost.state, "unresolved");
  assert.equal(ghost.href, null, "no-orphan law: unconfirmed peers never link");
  assert.equal(ghost.status, "partial");
});

test("[B-RP1] census anchors never become per-entity items", () => {
  const cards = relationCardsFor("locations", "level13", "en", "");
  const charCard = cards.find((c) => c.family === "character--scene-membership");
  assert.ok(charCard.items.every((i) => !i.key.includes("scene-class:")),
    "from:null scene-class census rows stay off entity cards (CH-6)");
});

test("[B-RP1] fail-closed density: 14 note tokens collapse into one form-counted row", () => {
  const cards = relationCardsFor("locations", "level13", "en", "");
  const docCard = cards.find((c) => c.family === "document--scene-membership");
  assert.ok(docCard, "inbound documents card must exist");
  assert.equal(docCard.items.length, 1, "dense tokens collapse");
  assert.equal(docCard.items[0].count, 14);
  assert.equal(docCard.items[0].label, "note:");
  assert.equal(docCard.items[0].href, null);
});

test("[B-RP1] minigame page: unrouted outfit peers echo as text with resolved chips + missing_fields", () => {
  const cards = relationCardsFor("minigames", "pinguin", "en", "");
  const card = cards.find((c) => c.family === "minigame--outfit-unlock");
  assert.ok(card, "outfit-unlock card must exist");
  const christmas = card.items.find((i) => i.label === "outfit:Chirfns");
  assert.ok(christmas, "unroutable outfit anchor echoes verbatim");
  assert.equal(christmas.state, "text");
  assert.equal(christmas.arrow, "→");
  assert.ok(christmas.extras.includes("Christmas"), "the row's own Clothes pointer resolves as a side chip");
  const original = card.items.find((i) => i.label === "outfit:original");
  assert.ok(original, "second unlock peer present");
  assert.deepEqual(original.missingFields, ["reflection targets unproven"], "named explicit-missing states ride through");
  assert.equal(original.status, "partial");
});

test("[B-RP1] mita page: machine-plane speaker-theme peer stays text with its curation status", () => {
  const cards = relationCardsFor("mita", "mita-usual", "en", "");
  const themeCard = cards.find((c) => c.family === "dialogue-speaker-theme--character");
  assert.ok(themeCard, "speaker theme family routes on mita pages");
  const item = themeCard.items.find((i) => i.label === "speaker-theme:Mita");
  assert.ok(item, "machine-plane anchor echoes verbatim");
  assert.equal(item.state, "text");
  assert.equal(item.href, null);
  assert.equal(item.status, "provisional-pending-ds1");
  assert.equal(item.arrow, "←", "the page sat on the to-side of the forward-only edge");
});

test("[B-RP1] endings page: dedicated tab owns achievement--ending; scalar anchoring still resolves", () => {
  assert.deepEqual(relationCardsFor("endings", "conditions-met", "en", ""), []);
  const anchored = edgesAnchoringPage("achievement--ending", "achievements", "ACHI_orphan");
  assert.equal(anchored.length, 1, "scalar-keyed pair anchors by column value");
  assert.equal(anchored[0].peer.form, "ending:");
  assert.equal(anchored[0].peer.id, "conditions-met");
  assert.equal(anchored[0].edge.scalars.achievement_id, "ACHI_orphan");
});

test("[B-RP1] cartridge pages ship no extra cards; META-ONLY families never render", () => {
  const cards = relationCardsFor("cartridges", "cart-mtashh", "en", "");
  assert.deepEqual(cards, []);
});

test("[B-RP1] dedicated-tab conversion path: bare-slug page anchoring over the registry reader", () => {
  const anchored = edgesAnchoringPage("character--scene-membership", "mita", "mita-usual");
  assert.equal(anchored.length, 3, "two mirrored level13 edges + one census-token edge");
  const linked = anchored.filter((a) => a.peer?.form === "scene:");
  assert.equal(linked.length, 2);
  for (const a of linked) {
    assert.equal(a.peer.id, "level13");
    assert.ok(["forward", "inverse"].includes(a.edge.direction));
  }
});

test("[B-RP1] consume-time census gate: disk drift from joins.json fails loud", async () => {
  const root2 = mkdtempSync(join(tmpdir(), `relcards-drift-${process.pid}`));
  const ex2 = join(root2, "extracted", "relinks");
  const rg2 = join(root2, "registry");
  mkdirSync(ex2, { recursive: true });
  mkdirSync(rg2, { recursive: true });
  writeFileSync(
    join(ex2, "minigame--choice-condition.jsonl"),
    [JSON.stringify({ direction: "forward", from: "minigame:a", to: "choice_flag:x", mechanism: "hard", status: "modeled" })].join("\n")
  );
  // registry pins TWO edges, disk holds ONE → consumer refuses the tree
  writeFileSync(
    join(rg2, "joins.json"),
    JSON.stringify({
      _meta: {},
      families: {
        "minigame--choice-condition": {
          binds: "fixture", file: "extracted/relinks/minigame--choice-condition.jsonl",
          schema_id: "fixture/1", anchor_mode: "endpoints",
          anchor_grammar: { from: ["minigame:"], to: ["choice_flag:"] },
          direction_handling: "forward-only",
          edge_count_expected: 2, edge_count_measured: 2,
          mechanisms: { hard: 2 }, statuses: { modeled: 2 },
        },
      },
    })
  );
  const prevRoot = process.env.MISIDE_CONTRACTS_ROOT;
  const prevExtracted = process.env.MISIDE_EXTRACTED_ROOT;
  process.env.MISIDE_CONTRACTS_ROOT = rg2;
  process.env.MISIDE_EXTRACTED_ROOT = join(root2, "extracted");
  try {
    // query-string import = fresh module instance = fresh registry cache
    const drifted = await import("../src/data/joins.ts?drifted=1");
    assert.throws(() => drifted.familyEdges("minigame--choice-condition"), /registry pins 2 edges/,
      "drift between disk and the accepted registry must throw at consume time");
  } finally {
    process.env.MISIDE_CONTRACTS_ROOT = prevRoot;
    process.env.MISIDE_EXTRACTED_ROOT = prevExtracted;
  }
});

test("[B-RP1] carry-law bite condition is stated once and bites exactly off hard/modeled", () => {
  assert.equal(provenanceBites("hard", "modeled"), false);
  assert.equal(provenanceBites("inferred", "modeled"), true);
  assert.equal(provenanceBites("hard", "partial"), true);
  assert.equal(provenanceBites(undefined, undefined), false);
  assert.ok(DENSE_TOKEN_LIMIT >= 1);
});

/* ---------------- B-RP2 fix round (rp1-vA findings F1–F4) ---------------- */

test("[B-RP2] award-site cards consume the FLAT grant-site payload of a REAL shipped row", () => {
  const cards = relationCardsFor("achievements", "ACHI_WinFIght", "en", "");
  const card = cards.find((c) => c.family === "achievement--award-site");
  assert.ok(card, "the grant-site card must exist on an achievement page");
  assert.equal(card.edgeCount, 2, "card carries the REGISTRY-measured family census");
  const real = card.items.find((i) => i.label.includes("Dialogue_3DText_#7081.txt"));
  assert.ok(real, "the flat level/file/method payload renders");
  assert.equal(
    real.label,
    "site:level6 · Dialogue_3DText_#7081.txt · AchievementGet",
    "label built from scalars.level/file + edge.method — the shape the corpus ships"
  );
  assert.equal(real.state, "text");
  assert.equal(real.mechanism, "hard");
  assert.ok(
    card.items.every((i) => !i.label.includes("<absent>")),
    "no manufactured absence may remain (rp1-vA F1)"
  );
});

test("[B-RP2] award-site fail-closed: a payload-less row names its missing keys", () => {
  const cards = relationCardsFor("achievements", "ACHI_bare", "en", "");
  const card = cards.find((c) => c.family === "achievement--award-site");
  assert.ok(card);
  assert.deepEqual(
    card.items.map((i) => i.label),
    ["site:award_site: <missing level/file>"],
    "absence stays typed and names the absent keys (spec §7 rule 2)"
  );
});

test("[B-RP2] method rides RelationEdge like mechanism/status (joins carry law)", async () => {
  const joins = await import("../src/data/joins.ts");
  const [withMethod] = joins.familyEdges("achievement--award-site");
  assert.equal(withMethod.method, "AchievementGet", "recorded derivation carried verbatim");
  assert.equal("method" in withMethod.scalars, false, "method stays provenance, not a scalar");
  const others = joins.familyEdges("character--scene-membership");
  assert.ok(others.length > 0);
  assert.ok(others.every((e) => e.method === null), "families without the column read null");
});

test("[B-RP2] paired endings link through the routed /endings tree (resolveAnchor ending:)", () => {
  const cards = relationCardsFor("achievements", "ACHI_real", "en", "");
  const card = cards.find((c) => c.family === "achievement--ending");
  assert.ok(card, "scalar-keyed pair routes on the achievements page");
  assert.equal(card.items.length, 1);
  const ending = card.items[0];
  assert.equal(ending.label, "Conditions Met", "owning-row name, never raw machine text");
  assert.equal(ending.href, "/endings/conditions-met");
  assert.equal(ending.state, "linked", "no-orphan confirmed via the endings dataset row");
});

test("[B-RP2] census kind-growth gate: an UNREGISTERED index kind fails loud, named", async () => {
  const { assertSearchCensus } = await import("../src/lib/search/searchSource.ts");
  const { LOCALES } = await import("../src/i18n/locales.ts");
  const pivot = LOCALES[0].code;
  const base = [
    { id: "level13", kind: "locations", title: "Level 13", text: "", url: "/locations/level13" },
  ];
  assert.doesNotThrow(
    () => assertSearchCensus(new Map([[pivot, base]])),
    "registered kinds alone still pass the gate"
  );
  const grown = new Map([
    [
      pivot,
      [
        ...base,
        { id: "widget-1", kind: "widgets", title: "Widget", text: "", url: "/widgets/widget-1" },
      ],
    ],
  ]);
  assert.throws(
    () => assertSearchCensus(grown),
    /unregistered kind "widgets"/,
    "a NEW routed entity kind must fail the emit by name, not drift through silently"
  );
});

/* ---------------- static greps: one consumption path per law ---------------- */

test("[B-RP1] static: the renderer reuses the shared chip; pages consume the registry path", () => {
  const siteRoot = join(import.meta.dirname, "..");
  const read = (p) => readFileSync(join(siteRoot, p), "utf8");
  const cards = read("src/components/entity/RelationCards.tsx");
  assert.match(cards, /ProvenanceChip/, "relation items render through the shared carry-law chip");
  assert.doesNotMatch(cards, /mechanism\s*!==\s*["']hard["']/,
    "the bite condition must NOT be re-implemented in the renderer (one statement of the law)");
  const route = read("src/components/routes/EntityDetailRoute.tsx");
  assert.match(route, /edgesAnchoringPage\(/, "converted tabs anchor through the registry reader");
  assert.match(route, /relationCardsFor\(/, "the relations tab consumes the card builder");
  assert.doesNotMatch(route, /depicts_character_id === data\.id/,
    "ad-hoc depicts filter is gone (family consumption only)");
  assert.doesNotMatch(route, /subject_character_id === data\.id/,
    "ad-hoc subject filter is gone (document--character family only)");
});

test("[B-RP1] static: search has exactly ONE index construction and ONE matching config", () => {
  const siteRoot = join(import.meta.dirname, "..");
  const field = readFileSync(join(siteRoot, "src/components/chrome/SearchField.tsx"), "utf8");
  assert.match(field, /createSearchIndex\(rows\)/, "browser side builds through the shared constructor");
  assert.doesNotMatch(field, /new MiniSearch/, "no second hand-rolled MiniSearch config may exist");
  const emitter = readFileSync(join(siteRoot, "scripts/emit-artifacts.mjs"), "utf8");
  assert.match(emitter, /buildAllLocaleSearchRows/, "emitter builds rows through the shared TS builder");
  assert.match(emitter, /assertSearchCensus/, "emitter reconciles against entities.json");
  assert.doesNotMatch(emitter, /function deslug|const KINDS = \[/,
    "the duplicated KINDS/deslug layer is gone");
});
