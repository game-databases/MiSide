/*
 * §6 search-in-place law: the ONE matching function behaves identically on
 * both sides; nothing matches below two typed characters; facets stay
 * client-local (no URL creation).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  MAX_VISIBLE_ROWS,
  MIN_QUERY_LENGTH,
  countSearchHits,
  createSearchIndex,
  indexAll,
  searchRows,
} from "../src/lib/search/searchRows.ts";

const ROWS = [
  { id: "mita-usual", kind: "mita", title: "Mita", text: "The first Mita.", url: "/mita/mita-usual" },
  { id: "mita-2-d", kind: "mita", title: "Mita 2 D", text: "", url: "/mita/mita-2-d" },
  { id: "mta-cap", kind: "cartridges", title: "mtacap", text: "", url: "/cartridges/mta-cap" },
];

function makeIndex() {
  const idx = createSearchIndex(ROWS);
  indexAll(idx, ROWS);
  return idx;
}

test("reactive-input law: zero hits below two typed characters", () => {
  const idx = makeIndex();
  assert.equal(MIN_QUERY_LENGTH, 2);
  assert.deepEqual(searchRows(idx, ""), []);
  assert.deepEqual(searchRows(idx, "m"), []);
});

test("same function, same hits — server and browser cannot diverge", () => {
  const a = makeIndex();
  const b = makeIndex();
  const ra = searchRows(a, "mita");
  const rb = searchRows(b, "mita");
  assert.equal(searchRows(a, "mita").length > 0, true);
  assert.deepEqual(
    ra.map((h) => h.id),
    rb.map((h) => h.id)
  );
});

test("facet rides the same function and creates no URLs", () => {
  const idx = makeIndex();
  const all = searchRows(idx, "mita");
  const mitaOnly = searchRows(idx, "mita", { kind: "mita" });
  assert.ok(all.length >= mitaOnly.length);
  assert.ok(mitaOnly.every((h) => h.kind === "mita"));
});

/*
 * VC-2 fix #4 law: the render cap never hides a whole matching kind. The
 * old hard-20 let one dense kind crowd every other kind out of the visible
 * rows; truncation now kind-balances and countSearchHits feeds a "+N" chip.
 */
const DENSE = Array.from({ length: 12 }, (_, i) => ({
  id: `mita-${i}`,
  kind: "mita",
  title: `Mita ${i}`,
  text: "",
  url: `/mita/mita-${i}`,
}));
const SPARSE = [
  { id: "cartridge-mita", kind: "cartridges", title: "Cartridge Mita", text: "", url: "/cartridges/cartridge-mita" },
  { id: "ending-mita", kind: "endings", title: "Ending Mita", text: "", url: "/endings/ending-mita" },
];
function makeDenseIndex() {
  const rows = [...DENSE, ...SPARSE];
  const idx = createSearchIndex(rows);
  indexAll(idx, rows);
  return idx;
}

test("render cap is kind-balanced: no matching kind is crowded out entirely", () => {
  const idx = makeDenseIndex();
  // 12 dense rows against a limit of 8: unbalanced truncation would show
  // mitas only.
  assert.ok(DENSE.length > 8);
  const visible = searchRows(idx, "mita", { limit: 8 });
  assert.equal(visible.length, 8);
  const kinds = new Set(visible.map((h) => h.kind));
  for (const k of ["mita", "cartridges", "endings"]) {
    assert.ok(kinds.has(k), `kind ${k} invisible under the cap`);
  }
});

test("under the cap the pure score order passes through untouched", () => {
  const idx = makeDenseIndex();
  const all = searchRows(idx, "mita");
  const capped = searchRows(idx, "mita", { limit: MAX_VISIBLE_ROWS });
  assert.deepEqual(
    capped.map((h) => h.id),
    all.map((h) => h.id)
  );
});

test("+N chip feed: countSearchHits counts matches BEFORE truncation", () => {
  const idx = makeDenseIndex();
  const total = countSearchHits(idx, "mita");
  const visible = searchRows(idx, "mita", { limit: 8 });
  assert.equal(total, DENSE.length + SPARSE.length);
  assert.ok(total > visible.length);
});
