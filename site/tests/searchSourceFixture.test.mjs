/*
 * B-RP1 — search-row builder READER-DERIVATION proof (fixture leg).
 *
 * Runs against a synthetic MISIDE_EXTRACTED_ROOT in its own process (the
 * readers cache per process): adding and removing a dataset row must add and
 * remove exactly the corresponding search row — proving the index derives
 * from reader output, never a hardcoded list. (The availability-gate law has
 * its own isolated process in searchSourceGate.test.mjs.)
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, rmSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const root = mkdtempSync(join(tmpdir(), `searchsrc-${process.pid}`));
const extracted = join(root, "extracted");
for (const d of [
  "data/characters",
  "data/scenes",
  "relinks",
  "localization/English",
]) {
  mkdirSync(join(extracted, d), { recursive: true });
}
process.env.MISIDE_EXTRACTED_ROOT = extracted;

function writePersonages(ids) {
  const rows = ids.map((id, i) => ({
    character_id: id,
    kind: "mita",
    name_loc: { category: "Menu", line_index: i },
  }));
  writeFileSync(
    join(extracted, "data", "characters", "personages.jsonl"),
    [
      JSON.stringify({ _meta: { schema: "fixture", row_count: rows.length } }),
      ...rows.map((r) => JSON.stringify(r)),
    ].join("\n") + "\n"
  );
}

// English needs all four characters categories present or the mita kind gates out
writeFileSync(
  join(extracted, "relinks", "locale_availability.jsonl"),
  ["Menu", "Personages", "Names", "Clothes"]
    .map(
      (category) =>
        JSON.stringify({
          kind: "category_presence",
          locale: "English",
          dataset: "characters",
          category,
          classification: "present",
          record_count: 10,
        })
    )
    .join("\n") + "\n"
);
writeFileSync(
  join(extracted, "localization", "English", "Menu.jsonl"),
  [
    JSON.stringify({ line_index: 0, text: "Fixture Mita A" }),
    JSON.stringify({ line_index: 1, text: "Fixture Mita B" }),
  ].join("\n") + "\n"
);

const { buildSearchRowsForLocale } = await import("../src/lib/search/searchSource.ts");

test("[B-RP1] search rows derive from reader output: a dataset row IS the search row", () => {
  // restore the full four-category ledger (the availability module caches its
  // first load per process, so this test runs AFTER the gated variant)
  const cells = ["Menu", "Personages", "Names", "Clothes"].map((category) =>
    JSON.stringify({
      kind: "category_presence",
      locale: "English",
      dataset: "characters",
      category,
      classification: "present",
      record_count: 10,
    })
  );
  writeFileSync(join(extracted, "relinks", "locale_availability.jsonl"), cells.join("\n") + "\n");

  writePersonages(["mita-a"]);
  let rows = buildSearchRowsForLocale("en");
  assert.deepEqual(
    rows.filter((r) => r.kind === "mita").map((r) => [r.id, r.title]),
    [["mita-a", "Fixture Mita A"]]
  );
  assert.equal(rows[0].url, "/mita/mita-a");

  // add one emitted row → one more index row; remove → gone
  writePersonages(["mita-a", "mita-b"]);
  rows = buildSearchRowsForLocale("en");
  assert.equal(rows.filter((r) => r.kind === "mita").length, 2);
  writePersonages(["mita-b"]);
  rows = buildSearchRowsForLocale("en");
  assert.deepEqual(
    rows.filter((r) => r.kind === "mita").map((r) => r.id),
    ["mita-b"],
    "removed entity disappears from the derived index"
  );
});
