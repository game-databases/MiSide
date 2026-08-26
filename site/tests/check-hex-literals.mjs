/*
 * AC S8 lint half: NO hex literal inside components/ui|kit outside the token
 * import. Values come only from tokens.css (tier-1 T2 rows); a hex here is an
 * uncited color and fails the build.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const HEX = /#[0-9a-fA-F]{3,8}\b/;

let failures = 0;
for (const scope of ["ui", "kit"]) {
  const dir = join(root, "src", "components", scope);
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (!statSync(p).isFile() || !/\.(tsx?|mjs)$/.test(f)) continue;
    const lines = readFileSync(p, "utf8").split("\n");
    lines.forEach((line, i) => {
      // strip line comments before matching so prose can't trip the lint
      const code = line.replace(/\/\/.*$/, "");
      if (HEX.test(code)) {
        console.error(`hex literal FAIL ${p}:${i + 1}: ${line.trim()}`);
        failures++;
      }
    });
  }
}

if (failures) process.exit(1);
console.log("hex lint OK: components/ui + components/kit are token-only");
