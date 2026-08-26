/*
 * AC S13: loc resolution is ARITHMETIC-FREE. All offsets were applied at
 * emit (TV −1 pin, dialogue `line_index = game_index − 1`, Clothes
 * `stringName − 1`); these tests resolve the contracts' pinned examples with
 * NO additional offset — any ±1 in the loader fails them.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveLoc } from "../src/data/resolveLoc.ts";

// tests/ → site/ ; corpus lives one level up at MiSide/extracted/
const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const PACK_ROOT = join(SITE_DIR, "..", "..");

function jsonl(relFromPackRoot) {
  return readFileSync(join(PACK_ROOT, relFromPackRoot), "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l));
}

test("TV −1 pin already applied at emit: fight name_loc → line 0 'Dairy Scandal'", () => {
  const rows = jsonl("extracted/data/cartridges/minigames.jsonl").filter(
    (r) => !r._meta
  );
  const fight = rows.find((r) => r.minigame_id === "fight");
  const pinguin = rows.find((r) => r.minigame_id === "pinguin");
  // emitted pointers carry the CONVERTED index (identity offset was rejected:
  // it lands Fight on Pinguin's slot and indexes Pinguin out of range)
  assert.deepEqual(fight.name_loc, { category: "TelevisionGames", line_index: 0 });
  assert.deepEqual(pinguin.name_loc, { category: "TelevisionGames", line_index: 1 });
  // resolving needs NO additional offset:
  assert.equal(resolveLoc("en", fight.name_loc), "Dairy Scandal");
  assert.equal(resolveLoc("en", pinguin.name_loc), "Penguin Piles");
});

test("characters pointer Menu[83] resolves mita-usual's shared name", () => {
  const row = jsonl("extracted/data/characters/personages.jsonl").find(
    (r) => r.character_id === "mita-usual"
  );
  assert.equal(resolveLoc("en", row.name_loc), "Mita"); // name_is_shared pair
});

test("Clothes pin: line_index 10 resolves 'School' with zero extra shift", () => {
  // achievements contract: ClothCompleted site FIIdClSchool → Clothes#line_index=10
  assert.equal(resolveLoc("en", { category: "Clothes", line_index: 10 }), "School");
});

test("dialogue −1 contract already applied: LD4 line 0 is 'Mita?'", () => {
  assert.equal(
    resolveLoc("en", { category: "LocationDialogue Location4", line_index: 0 }),
    "Mita?"
  );
});

test("out-of-range cell resolves empty string (filler handled upstream)", () => {
  assert.equal(resolveLoc("en", { category: "Menu", line_index: 99999 }), "");
});

test("per-locale resolution: ru pivot of the same pointer differs from en", () => {
  const ru = resolveLoc("ru", { category: "LocationDialogue Location4", line_index: 0 });
  assert.notEqual(ru, "Mita?"); // same pointer, locale's own string
});
