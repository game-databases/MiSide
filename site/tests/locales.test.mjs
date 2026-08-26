/*
 * §3.1: the 34-row locale table unit-tested against the availability ledger's
 * locale vocabulary — a ledger locale with no mapping row fails the build.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const EXTRACTED = join(SITE_DIR, "..", "..", "extracted");

test("ledger locales ↔ table dirNames reconcile 34↔34", async () => {
  const { LOCALES, PREFIXED_LOCALES, getLocale, localeByDirName } = await import(
    "../src/i18n/locales.ts"
  );
  const ledgerLocales = new Set(
    readFileSync(join(EXTRACTED, "relinks/locale_availability.jsonl"), "utf8")
      .split("\n")
      .filter((l) => l.trim())
      .map((l) => JSON.parse(l).locale)
      .filter(Boolean)
  );
  assert.equal(LOCALES.length, 34);
  assert.equal(PREFIXED_LOCALES.length, 33);
  assert.equal(getLocale("en").prefix, "");
  for (const dirName of ledgerLocales) {
    assert.ok(localeByDirName(dirName), `ledger locale without a mapping row: ${dirName}`);
  }
  // the reverse: every table dirName appears in the ledger
  for (const def of LOCALES) {
    assert.ok(
      ledgerLocales.has(def.dirName),
      `table dir absent from ledger: ${def.dirName}`
    );
  }
});

test("exactly two declared chrome aliases; RTL only ar/ar-EG per spec letter", async () => {
  const { LOCALES } = await import("../src/i18n/locales.ts");
  const aliased = LOCALES.filter((l) => l.chromeAlias);
  assert.deepEqual(
    aliased.map((l) => [l.code, l.chromeAlias]),
    [
      ["ar-EG", "ar"],
      ["ru-x-prerev", "ru"],
    ]
  );
  const rtl = LOCALES.filter((l) => l.dir === "rtl").map((l) => l.code);
  assert.deepEqual(rtl.sort(), ["ar", "ar-EG"]);
});
