/*
 * TW-MV1 — launch gates around the map piece:
 *  - sitemap partitions: map routes gated guides-style (ledger availability),
 *    /locations/<scene_id> pages already enumerated (AC MV-4 substrate);
 *  - island discipline: Leaflet importable ONLY inside components/map (AC
 *    MV-8 static slice; the bundle assert itself stays with check-cwv);
 *  - MV-9 negative gate self-test: check-no-third-party-maps.mjs still trips
 *    on a canary AND passes clean on the real tree;
 *  - token guard: no uncited hex anywhere under src/components/map (§9 law,
 *    AC-S8 defect class — the existing check-hex-literals.mjs covers ui/kit).
 */
import "./registerAliasLoader.mjs";
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync, readdirSync, writeFileSync, mkdirSync, rmSync, statSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = join(SITE_DIR, "..");
const TMP = join(SITE_ROOT, "tmp");

// contracts.ts derives extractedRoot() from cwd — pin it so the suite runs
// from any directory (npm test runs with cwd=site).
process.env.MISIDE_EXTRACTED_ROOT ??= join(SITE_ROOT, "..", "extracted");

/* ---------------- sitemap partitions ---------------- */

test("map routes ride guides-style availability gating in the sitemap partitions", async () => {
  const { sitemapPartitionIds } = await import("@/lib/sitemapPartitions.ts"); // alias resolved by tests/aliasLoader.mjs
  const ids = sitemapPartitionIds();
  const localesOf = (section) =>
    new Set(ids.filter((id) => id.startsWith(`${section}@`)).map((id) => id.slice(section.length + 1)));
  const mapLocales = localesOf("map");
  const guideLocales = localesOf("guides");
  assert.ok(guideLocales.size > 0, "no guides partitions — availability ledger unreadable");
  assert.deepEqual(
    [...mapLocales].sort(),
    [...guideLocales].sort(),
    "/map must be admitted per-locale exactly like the guides section (content-bearing gating), not unconditionally"
  );
});

test("locations partition enumerates every scene-locked page /locations/<scene_id>", async () => {
  const { sitemapPartitionIds, partitionUrls } = await import("@/lib/sitemapPartitions.ts");
  const { LOCALES } = await import("@/i18n/locales.ts");
  const { sceneIds } = await import("./mapFixtures.mjs");
  const scenes = sceneIds();
  assert.equal(scenes.length, 24, "corpus drift: scene count changed");
  let checked = 0;
  for (const id of sitemapPartitionIds()) {
    if (!id.startsWith("locations@")) continue;
    const code = id.slice(id.lastIndexOf("@") + 1);
    const def = LOCALES.find((l) => l.code === code);
    assert.ok(def, `partition references unknown locale ${code}`);
    const urls = partitionUrls(id);
    for (const scene of scenes) {
      assert.ok(urls.includes(`${def.prefix}/locations/${scene}`),
        `${id}: ${def.prefix}/locations/${scene} missing from the locations partition`);
      checked++;
    }
  }
  assert.ok(checked > 0, "no locations partitions found");
});

/* ---------------- island discipline (MV-8 static slice) ---------------- */

test("marker-shape suite's routed-segment mirror matches routes.ts KIND_SEGMENT", async () => {
  const { KIND_SEGMENT } = await import("@/lib/routes.ts");
  // keep in sync with ROUTED_SEGMENTS in mapMarkerShape.test.mjs
  assert.equal(KIND_SEGMENT.cartridges, "cartridges");
  assert.equal(KIND_SEGMENT.profiles, "lore/profiles");
  assert.equal(KIND_SEGMENT.minigames, "minigames");
});

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === ".next") continue;
    const p = join(dir, entry);
    const st = statSync(p);
    if (st.isDirectory()) yield* walk(p);
    else if (/\.(mjs|js|ts|tsx)$/.test(entry)) yield p;
  }
}

test("Leaflet stays inside the map island — no import outside src/components/map", () => {
  const offenders = [];
  for (const scope of ["src/app", "src/components", "src/lib", "src/data"]) {
    const dir = join(SITE_ROOT, scope);
    if (!existsSync(dir)) continue;
    for (const file of walk(dir)) {
      if (file.includes(join("components", "map"))) continue;
      const text = readFileSync(file, "utf8");
      if (/from\s+["']leaflet["']|import\(\s*["']leaflet["']\s*\)/.test(text)) offenders.push(file);
    }
  }
  assert.deepEqual(offenders, [], `Leaflet leaked out of the island: ${offenders.join(", ")}`);
});

/* ---------------- token guard (§9 / AC-S8 class) ---------------- */

const HEX = /#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/;

test("token guard: no raw hex in map components — color-mix over tier-1 rows only (OQ-10)", () => {
  const failures = [];
  const mapDir = join(SITE_ROOT, "src", "components", "map");
  for (const f of readdirSync(mapDir)) {
    if (!/\.(tsx?|mjs)$/.test(f)) continue;
    const p = join(mapDir, f);
    if (!statSync(p).isFile()) continue;
    readFileSync(p, "utf8").split("\n").forEach((line, i) => {
      const code = line.replace(/\/\/.*$/, ""); // strip line comments like the ui/kit lint
      if (HEX.test(code)) failures.push(`${p}:${i + 1}: ${line.trim()}`);
    });
  }
  assert.deepEqual(failures, [], `uncited hex under src/components/map:\n  ${failures.join("\n  ")}`);
});

/* ---------------- MV-9 negative-gate self-test ---------------- */

test("MV-9: no-third-party-maps gate trips on a canary and passes the real tree", () => {
  const scriptSrc = join(SITE_ROOT, "scripts", "check-no-third-party-maps.mjs");
  const root = join(TMP, `mv1-gate-selftest-${process.pid}`);
  try {
    mkdirSync(join(root, "scripts"), { recursive: true });
    mkdirSync(join(root, "src"), { recursive: true });
    copyFileSyncSafe(scriptSrc, join(root, "scripts", "check-no-third-party-maps.mjs"));
    writeFileSync(join(root, "src", "canary.tsx"), 'export const embed = "https://www.mapgenie.io/maps/miside";\n');

    const trip = spawnSync(process.execPath, [join(root, "scripts", "check-no-third-party-maps.mjs")], {
      cwd: root, encoding: "utf8",
    });
    assert.equal(trip.status, 1, `canary must FAIL the gate (status ${trip.status}): ${trip.stdout ?? ""}${trip.stderr ?? ""}`);
    assert.match(trip.stderr ?? "", /mapgenie/, "gate must name the banned host it caught");

    const clean = spawnSync(process.execPath, [scriptSrc], { cwd: SITE_ROOT, encoding: "utf8" });
    assert.equal(clean.status, 0, `real tree must pass the gate: ${clean.stderr ?? ""}`);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

function copyFileSyncSafe(from, to) {
  writeFileSync(to, readFileSync(from, "utf8"));
}
