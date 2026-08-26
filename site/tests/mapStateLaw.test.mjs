/*
 * TW-MV1 — mapState v2 history law (A-MV1 OQ-5, AC MV-3 unit core).
 *
 * Spec §5 mapState.ts row: "replaceState for filter toggles, focus changes,
 * focus clear, and ?kinds= edits (typing-law); pushState on scene change so
 * Back walks the scene trail; cold load restores whatever the URL carries."
 *
 * The landed API expresses the verbs as writeMapHistory(query, mode) call
 * sites in MapViewer.tsx (the single push site is the scene handler), with
 * parseMapState/buildMapSearch as the pure grammar. This file unit-tests the
 * grammar and statically pins the verb discipline at every call site.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const MAP_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "components", "map");
const FOCUS = { kind: "cartridges", slug: "mtal" };

async function mapState() {
  return import("../src/components/map/mapState.ts");
}

test("v0 regression: focus grammar keeps parsing + formatting", async () => {
  const ns = await mapState();
  const parsed = ns.parseFocus(
    new URLSearchParams("focus=cartridges:mtacap&scene=level9")
  );
  assert.deepEqual(parsed, { kind: "cartridges", slug: "mtacap", scene: "level9" });
  assert.equal(ns.formatFocus(FOCUS), "?focus=cartridges%3Amtal");
});

test("MV-3 core: deep-link cold load restores scene + filter + focus", async () => {
  const ns = await mapState();
  const state = ns.parseMapState(
    new URLSearchParams("focus=cartridges:mtal&scene=level10&kinds=cartridge")
  );
  assert.equal(state.scene, "level10");
  assert.equal(state.focus.kind, "cartridges");
  assert.equal(state.focus.slug, "mtal");
  assert.deepEqual(state.kinds, ["cartridge"]);
  // no kinds param = no explicit selection (all enabled), not an empty set
  const bare = ns.parseMapState(new URLSearchParams("focus=cartridges:mtal"));
  assert.equal(bare.kinds, null);
});

test("kinds grammar is ordered + deduped both directions; Show All vs explicit-empty distinct", async () => {
  const ns = await mapState();
  // parse side: first-seen order kept, repeats dropped, empty segments dropped
  assert.deepEqual(
    ns.parseMapState(new URLSearchParams("kinds=minigame_access,cartridge,minigame_access")).kinds,
    ["minigame_access", "cartridge"]
  );
  // build side: deduped, order preserved
  assert.equal(ns.buildMapSearch({}, { kinds: ["b", "a", "b"] }), "?kinds=b%2Ca");
  // [] stays EXPLICIT (?kinds= — nothing enabled); null REMOVES the param (Show All)
  assert.equal(ns.buildMapSearch({}, { kinds: [] }).startsWith("?kinds="), true);
  assert.equal(ns.buildMapSearch({}, { kinds: null }), "");
  // round trip
  const q = ns.buildMapSearch({}, { scene: "level10", kinds: ["safe", "cartridge"] });
  const rt = ns.parseMapState(new URLSearchParams(q.replace(/^\?/, "")));
  assert.equal(rt.scene, "level10");
  assert.deepEqual(rt.kinds, ["safe", "cartridge"]);
});

test("writeMapHistory is a safe no-op off-browser (SSG render must not throw)", async () => {
  const ns = await mapState();
  assert.equal(typeof window, "undefined");
  ns.writeMapHistory("?focus=cartridges:mtacap", "push");
  ns.writeMapHistory("", "replace");
});

test("OQ-5 static pin: exactly ONE push site (scene change); every other writer replaces", () => {
  const src = readFileSync(join(MAP_DIR, "MapViewer.tsx"), "utf8");
  const sites = [];
  const lines = src.split("\n");
  lines.forEach((line, i) => {
    if (/writeMapHistory\(/.test(line)) {
      const body = lines.slice(i, i + 8).join("\n");
      const mode = /"push"/.test(body) ? "push" : /"replace"/.test(body) ? "replace" : "?";
      sites.push({ line: i + 1, mode, body });
    }
  });
  assert.ok(sites.length >= 3, `expected the filter/focus/scene writers, found ${sites.length}`);
  const pushes = sites.filter((s) => s.mode === "push");
  assert.equal(pushes.length, 1, `the law allows exactly one push site (scene change); got ${pushes.length} at lines ${pushes.map((p) => p.line).join(", ")}`);
  assert.match(pushes[0].body, /selectScene|scene/, "the single push site must be the scene-change writer");
  for (const s of sites.filter((x) => x.mode !== "push")) {
    assert.equal(s.mode, "replace", `line ${s.line}: non-scene writers must replaceState`);
  }
});
