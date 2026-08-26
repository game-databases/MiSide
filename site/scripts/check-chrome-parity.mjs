/*
 * AC S4: key-set equality across all chrome/<locale>.json files.
 * Exit 0 = all 34 identical key sets + only the two declared aliases pass
 * (aliased file content equals its target verbatim). Injected key drift →
 * exit ≠ 0. Also fails on English passthrough detection is NOT possible here
 * (values are authored); parity is structural.
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "src",
  "i18n",
  "chrome"
);

const DECLARED_ALIASES = { "ru-x-prerev": "ru", "ar-EG": "ar" };
const EXPECTED_COUNT = 34;

const files = readdirSync(dir).filter((f) => f.endsWith(".json"));
if (files.length !== EXPECTED_COUNT) {
  console.error(
    `parity FAIL: expected ${EXPECTED_COUNT} chrome files, found ${files.length}`
  );
  process.exit(1);
}

const keySets = new Map();
for (const f of files) {
  const code = f.replace(/\.json$/, "");
  const obj = JSON.parse(readFileSync(join(dir, f), "utf8"));
  keySets.set(code, Object.keys(obj).sort());
}

// 1. identical key sets across all files
const baseCode = "en";
const baseKeys = JSON.stringify(keySets.get(baseCode));
for (const [code, keys] of keySets) {
  if (JSON.stringify(keys) !== baseKeys) {
    console.error(`parity FAIL: ${code} key set drifts from en`);
    process.exit(1);
  }
}

// 2. alias discipline: ONLY the two declared aliases may exist, and their
//    values must mirror the target verbatim (the file-count gate above
//    already rejects any undeclared extra chrome file)
for (const [alias, target] of Object.entries(DECLARED_ALIASES)) {
  const a = JSON.parse(readFileSync(join(dir, `${alias}.json`), "utf8"));
  const t = JSON.parse(readFileSync(join(dir, `${target}.json`), "utf8"));
  for (const k of Object.keys(t)) {
    if (a[k] !== t[k]) {
      console.error(`parity FAIL: ${alias}[${k}] does not mirror ${target}`);
      process.exit(1);
    }
  }
}

console.log(`chrome parity OK: ${files.length} locales, identical key sets`);
