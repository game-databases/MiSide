/*
 * AC S10 runner: CWV lab traces per template × canonical locale against a
 * running production server (next start). Uses Lighthouse via npx when
 * available; reports honestly and exits non-zero on budget breach.
 *
 *   node scripts/check-cwv.mjs [--base http://localhost:3000]
 *
 * Lighthouse is NOT bundled as a devDependency (install weight vs the C:
 * disk floor) — CI installs it (`npm i -g lighthouse` in the staged workflow).
 */
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const base =
  process.argv.includes("--base")
    ? process.argv[process.argv.indexOf("--base") + 1]
    : "http://localhost:3000";

const cfg = JSON.parse(readFileSync(join(root, "cwv.budgets.json"), "utf8"));

function have(name) {
  return spawnSync(name, ["--version"], { shell: true }).status === 0;
}

if (!have("lighthouse")) {
  console.log(
    "check-cwv SKIP: lighthouse CLI not installed. Run `npx lighthouse` " +
      "(CI workflow installs it). Budgets live in cwv.budgets.json."
  );
  process.exit(0);
}

let failures = 0;
for (const t of cfg.templates) {
  for (const ff of t.formFactors) {
    const out = spawnSync(
      "lighthouse",
      [
        `${base}${t.url}`,
        `--form-factor=${ff}`,
        "--screenEmulation.mobile=" + (ff === "mobile"),
        "--chrome-flags=headless",
        "--output=json",
        "--quiet",
      ],
      { encoding: "utf8", shell: true }
    );
    if (out.status !== 0 || !out.stdout) {
      console.error(`cwv ERROR ${t.template}/${ff}: lighthouse run failed`);
      failures++;
      continue;
    }
    const audit = JSON.parse(out.stdout.slice(out.stdout.indexOf("{")));
    const lcp = audit.audits?.["largest-contentful-paint"]?.numericValue;
    const cls = audit.audits?.["cumulative-layout-shift"]?.numericValue;
    const bad =
      (typeof lcp === "number" && lcp > cfg.budgets.lcpMs) ||
      (typeof cls === "number" && cls > cfg.budgets.cls);
    console.log(
      `${bad ? "cwv FAIL" : "cwv OK  "} ${t.template}/${ff} ` +
        `LCP=${Math.round(lcp ?? -1)}ms CLS=${(cls ?? -1).toFixed(4)}`
    );
    if (bad) failures++;
  }
}
process.exit(failures > 0 ? 1 : 0);
