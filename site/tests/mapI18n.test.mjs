/*
 * TW-MV1 — chrome i18n for the map viewer (AC MV-5 core + MV-7 RTL leg,
 * automated slice).
 *
 * Spec §10 pins the new key set; all 34 locale files ship (none staged) and
 * `scripts/check-chrome-parity.mjs` enforces key-set equality — this test
 * asserts the MAP keys exist in every file, are non-empty, and that the ar
 * leg is real Arabic script (the RTL trace at 375px itself stays in the
 * scripted-trace lane).
 *
 * [M5-PENDING] tests go red until the M5 key freeze lands; that redness is
 * the i18n gate doing its job.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const CHROME_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "i18n", "chrome");

/** Spec §10 additions ("final wording at implementation" — keys, not values). */
export const NEW_MAP_KEYS = [
  "map.scenes",
  "map.sceneLocked",
  "map.showAll",
  "map.hideAll",
  "map.resetView",
  "map.filterSearch",
  "map.resultsCount",
  "map.awaitingTransform",
  "map.sceneGranular",
  "map.unplaced",
  "map.popover.openPage",
  "map.chapterUnlabeled",
];

/** v0 keys the piece must not regress. */
const EXISTING_KEYS = ["nav.map", "map.openMap", "map.pendingPlacement"];

function chromeFiles() {
  return readdirSync(CHROME_DIR).filter((f) => f.endsWith(".json")).sort();
}

test("chrome layer ships exactly 34 locale files", () => {
  assert.equal(chromeFiles().length, 34);
});

test("[M5-PENDING] MV-5: every new map.* key exists across ×34 locales incl ar/fa", () => {
  const missing = [];
  const empty = [];
  for (const f of chromeFiles()) {
    const obj = JSON.parse(readFileSync(join(CHROME_DIR, f), "utf8"));
    for (const key of [...EXISTING_KEYS, ...NEW_MAP_KEYS]) {
      if (!(key in obj)) missing.push(`${f}:${key}`);
      else if (typeof obj[key] !== "string" || obj[key].length === 0) empty.push(`${f}:${key}`);
    }
  }
  assert.deepEqual(missing, [], `missing map chrome keys:\n  ${missing.join("\n  ")}`);
  assert.deepEqual(empty, [], `empty map chrome values:\n  ${empty.join("\n  ")}`);
});

test("RTL vocabulary: exactly ar + ar-EG declared rtl and propagated to <html>", async () => {
  const { LOCALES } = await import("../src/i18n/locales.ts");
  assert.deepEqual(
    LOCALES.filter((l) => l.dir === "rtl").map((l) => l.code),
    ["ar", "ar-EG"]
  );
  // layout must propagate dir to the html shell (MV-7's mirroring substrate)
  const layout = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "..", "src", "app", "[locale]", "layout.tsx"),
    "utf8"
  );
  assert.match(layout, /dir=\{?\s*def\.dir/, "[locale] layout must bind dir from the locale def");
});

test("[M5-PENDING] MV-7 RTL leg data-side: ar renders real Arabic for the new map keys", () => {
  const ar = JSON.parse(readFileSync(join(CHROME_DIR, "ar.json"), "utf8"));
  const arabic = /[؀-ۿ]/;
  let withScript = 0;
  for (const key of NEW_MAP_KEYS) {
    const value = ar[key];
    assert.ok(typeof value === "string" && value.length > 0, `ar.json:${key} missing/empty`);
    if (arabic.test(value)) withScript++;
    // never leaks another locale's text under the ar URL
    assert.ok(!/^[\x00-\x7F]*$/.test(value), `ar.json:${key} is bare ASCII passthrough ("${value}")`);
  }
  assert.ok(withScript >= Math.ceil(NEW_MAP_KEYS.length / 2),
    `only ${withScript}/${NEW_MAP_KEYS.length} ar map keys carry Arabic script — placeholder translation fails the RTL leg`);
});
