/*
 * AC S7 / FRAMEWORK §8 launch gate: negative embed grep. The build FAILS on
 * mapgenie.io and sibling third-party map embeds anywhere in shipped site
 * source or emitted public artifacts. Owned scene maps or none — never
 * embedded.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const SELF = fileURLToPath(import.meta.url);
const BANNED_HOSTS = [
  ["mapgenie", "io"].join("."),
  ["mapgenie", "gg"].join("."),
  "mapgenie",
  ["maps", "googleapis", "com"].join("."),
  ["maps", "google", "com/maps/embed"].join("."),
  ["mapbox", "com"].join("."),
  ["maptiler", "com"].join("."),
  ["thunderforest", "com"].join("."),
  ["wiki", "gg/maps"].join("."), // wiki.gg embedded map surfaces
];

const SKIP_DIRS = new Set(["node_modules", ".next", ".git"]);

function* walk(dir) {
  for (const entry of readdirSync(dir)) {
    if (SKIP_DIRS.has(entry)) continue;
    const p = join(dir, entry);
    if (p === SELF) continue; // this checker names the banned hosts by necessity
    const st = statSync(p);
    if (st.isDirectory()) yield* walk(p);
    else if (/\.(mjs|js|ts|tsx|json|html|css|txt|xml|mdx|md)$/.test(entry)) yield p;
  }
}

let hits = 0;
// content pipeline C9: authored article sources join the negative grep
for (const scope of ["src", "scripts", "public", "content"]) {
  const dir = join(root, scope);
  try {
    statSync(dir);
  } catch {
    continue;
  }
  for (const file of walk(dir)) {
    const text = readFileSync(file, "utf8");
    for (const host of BANNED_HOSTS) {
      let idx = text.indexOf(host);
      while (idx !== -1) {
        console.error(`third-party map embed FOUND: ${host} in ${file}`);
        hits++;
        idx = text.indexOf(host, idx + 1);
      }
    }
  }
}

if (hits > 0) {
  console.error(`no-third-party-maps FAIL: ${hits} hit(s)`);
  process.exit(1);
}
console.log("no-third-party-maps OK: zero banned embeds");
