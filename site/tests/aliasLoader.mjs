/*
 * TW-MV1 loader hook: resolves the site's "@/..." alias for plain
 * `node --test` runs (no tsconfig paths support in Node ESM). Test-support
 * only; register via registerAliasLoader.mjs before importing @-aliased
 * modules (e.g. src/lib/sitemapPartitions.ts).
 */
import { existsSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SRC_ROOT = new URL("../src/", import.meta.url);
const SHIM_ROOT = new URL("./shims/", import.meta.url);

/** JSX leaves no test can execute — redirected to behavior-equivalent shims. */
const TSX_SHIMS = new Map([
  ["entityView.tsx", "entityView.mjs"],
]);

const CANDIDATE_SUFFIXES = ["", ".ts", ".tsx", ".mjs", "/index.ts"];

/** Route a resolved .tsx module to its shim, or fail with a legible reason. */
function redirectTsx(resolution) {
  const path = fileURLToPath(resolution.url);
  const base = path.split(/[\\/]/).pop();
  if (base.endsWith(".tsx")) {
    if (TSX_SHIMS.has(base)) {
      return { ...resolution, url: new URL(TSX_SHIMS.get(base), SHIM_ROOT).href };
    }
    const e = new Error(
      `TW-MV1: ${base} contains JSX and cannot load under node --test. ` +
      `Either keep the tested logic in a .ts module or add a shim in tests/shims/ + TSX_SHIMS.`
    );
    e.__tw_mv1_tsx = true;
    throw e;
  }
  return resolution;
}

export async function resolve(specifier, context, nextResolve) {
  if (specifier.startsWith("@/")) {
    const rel = specifier.slice(2);
    for (const suffix of CANDIDATE_SUFFIXES) {
      const candidate = new URL(rel + suffix, SRC_ROOT);
      if (existsSync(fileURLToPath(candidate)) && statSync(fileURLToPath(candidate)).isFile()) {
        return redirectTsx({ url: candidate.href, shortCircuit: true });
      }
    }
  }
  // TS-style EXTENSIONLESS relative imports ("./entityView") — Node ESM
  // refuses them; retry with the usual TS suffixes.
  if (/^\.{1,2}\//.test(specifier) && !/\.[cm]?js(\?|$)/.test(specifier)) {
    try {
      return await nextResolve(specifier, context);
    } catch (err) {
      if (err?.code !== "ERR_MODULE_NOT_FOUND") throw err;
      for (const suffix of [".ts", ".tsx", "/index.ts"]) {
        try {
          const hit = await nextResolve(specifier + suffix, context);
          return redirectTsx(hit);
        } catch (e) {
          if (e?.__tw_mv1_tsx) throw e;
          /* try next */
        }
      }
      throw err;
    }
  }
  return nextResolve(specifier, context);
}
