/*
 * B-RP1 — search-row builder AVAILABILITY-GATE proof (fixture leg, isolated
 * process because the ledger reader caches its first load).
 *
 * With the characters category ledger INCOMPLETE for English, the route tree
 * would notFound() the mita kind — so the index must ship no mita rows.
 * A search row may never target a URL that 404s.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, mkdtempSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const root = mkdtempSync(join(tmpdir(), `searchgate-${process.pid}`));
const extracted = join(root, "extracted");
for (const d of ["data/characters", "relinks", "localization/English"]) {
  mkdirSync(join(extracted, d), { recursive: true });
}
process.env.MISIDE_EXTRACTED_ROOT = extracted;

// personages row exists on disk…
writeFileSync(
  join(extracted, "data", "characters", "personages.jsonl"),
  [
    JSON.stringify({ _meta: { schema: "fixture", row_count: 1 } }),
    JSON.stringify({
      character_id: "mita-a",
      kind: "mita",
      name_loc: { category: "Menu", line_index: 0 },
    }),
  ].join("\n") + "\n"
);
writeFileSync(
  join(extracted, "localization", "English", "Menu.jsonl"),
  [JSON.stringify({ line_index: 0, text: "Fixture Mita A" })].join("\n") + "\n"
);
// …but the ledger lacks the Personages category: kind unavailable
writeFileSync(
  join(extracted, "relinks", "locale_availability.jsonl"),
  ["Menu", "Names", "Clothes"]
    .map((category) =>
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

const { buildSearchRowsForLocale } = await import("../src/lib/search/searchSource.ts");

test("[B-RP1] an unavailable kind ships no search rows (no rows pointing at 404s)", () => {
  const rows = buildSearchRowsForLocale("en");
  assert.equal(rows.filter((r) => r.kind === "mita").length, 0);
});
