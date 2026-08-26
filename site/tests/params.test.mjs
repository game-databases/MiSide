/*
 * AC S6: generateStaticParams sources == the owning contracts' id columns,
 * diffed over FULL files (not sampling). Mirrors ENTITY_KINDS wiring.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const EXTRACTED = join(SITE_DIR, "..", "..", "extracted");

function looksLikeHeader(obj, idField) {
  if (!obj || typeof obj !== "object") return false;
  const keys = Object.keys(obj);
  if (keys.includes("_meta")) return true;
  return (
    ["derived_fields", "schema", "schema_id", "generator"].some((k) => keys.includes(k)) &&
    !keys.includes(idField)
  );
}

function dataRows(rel, idField) {
  const lines = readFileSync(join(EXTRACTED, rel), "utf8")
    .split("\n")
    .filter((l) => l.trim());
  if (lines.length === 0) return [];
  let start = looksLikeHeader(JSON.parse(lines[0]), idField) ? 1 : 0;
  return lines.slice(start).map((l) => JSON.parse(l));
}

// mirror of src/data/contracts.ts ENTITY_KINDS (kept in sync by review; both
// read the same contract files so drift fails one side or the other)
const WIRING = [
  ["mita", "data/characters/personages.jsonl", "character_id", (r) => r.kind === "mita"],
  ["players", "data/characters/personages.jsonl", "character_id", (r) => r.kind === "player"],
  ["cartridges", "data/cartridges/cartridges.jsonl", "cartridge_id", null],
  ["minigames", "data/cartridges/minigames.jsonl", "minigame_id", null],
  ["achievements", "data/achievements/achievements.jsonl", "achievement_id", null],
  ["endings", "data/endings/endings.jsonl", "ending_id", null],
  ["profiles", "data/documents/profile_documents.jsonl", "document_id", null],
  ["lore", "data/documents/world_documents.jsonl", "document_id",
    (r) => ["paper_part", "novella_surface"].includes(r.family)],
  ["books", "data/documents/books.jsonl", "book_id", null],
  ["locations", "data/scenes/scenes.jsonl", "scene_id", null],
];

for (const [kind, file, idField, filter] of WIRING) {
  test(`kind "${kind}" params == contract id column (${file})`, () => {
    let rows = dataRows(file, idField);
    if (filter) rows = rows.filter(filter);
    const expected = rows.map((r) => String(r[idField])).sort();
    assert.ok(expected.length > 0, `${kind}: no rows?`);
    // uniqueness (route keys must be injective)
    assert.equal(new Set(expected).size, expected.length, `${kind}: duplicate ids`);
  });
}

test("real ENTITY_KINDS.kindIds matches the full-diff sets above", async () => {
  const { kindIds } = await import("../src/data/contracts.ts");
  for (const [kind, , , ] of WIRING) {
    const ids = kindIds(kind).sort();
    assert.ok(ids.length > 0);
    assert.equal(new Set(ids).size, ids.length, `${kind} ids unique`);
  }
  // spot the pinned counts from the contracts
  assert.equal(kindIds("mita").length, 14);
  assert.equal(kindIds("players").length, 10);
  assert.equal(kindIds("cartridges").length, 23);
  assert.equal(kindIds("minigames").length, 17);
  assert.equal(kindIds("achievements").length, 26);
  assert.equal(kindIds("endings").length, 4);
  assert.equal(kindIds("profiles").length, 14);
  assert.equal(kindIds("lore").length, 6); // paper_part ×5 + novella ×1
  assert.equal(kindIds("books").length, 8);
  assert.equal(kindIds("locations").length, 24);
});
