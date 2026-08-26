/*
 * LEAF dataset-file reader — the bottom of the server-reader layer (no
 * imports above it, so both contracts.ts and joins.ts can sit on one copy;
 * two jsonl loaders that can drift was the defect class B-RP1 removes).
 *
 * Every .jsonl dataset's FIRST line is a {"_meta": …} header (contracts
 * §Files); data rows follow one JSON object per line. The _meta line is
 * parsed and exposed, never skipped silently.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

/** Repo-root extracted/ (override for exotic checkouts; build runs with cwd=site). */
export function extractedRoot(): string {
  return (
    process.env.MISIDE_EXTRACTED_ROOT ?? join(process.cwd(), "..", "extracted")
  );
}

/** Repo-root contracts/registry/ (the ACCEPTED registries; env-overridable for fixtures). */
export function contractsRegistryRoot(): string {
  return (
    process.env.MISIDE_CONTRACTS_ROOT ??
    join(process.cwd(), "..", "contracts", "registry")
  );
}

export interface JsonlFile<T> {
  meta: Record<string, unknown> | null;
  rows: T[];
}

/*
 * Two _meta header shapes exist in the corpus (measured 2026-08-25):
 *  • WRAPPED: {"_meta": {...}} — characters, cartridges, scenes, dialogue
 *    graphs, markers.
 *  • BARE: a header object as line 1 without the "_meta" key (carries
 *    build_id / derived_fields / schema keys instead) — documents family.
 * Files may also be EMPTY by contract (endings relink launch-member) or carry
 * no header at all (achievements/endings/dialogue data files, ledger files).
 */
function looksLikeHeader(obj: unknown, idField?: string): boolean {
  if (!obj || typeof obj !== "object") return false;
  const keys = Object.keys(obj as Record<string, unknown>);
  if (keys.includes("_meta")) return true;
  return (
    ["derived_fields", "schema", "schema_id", "generator"].some((k) =>
      keys.includes(k)
    ) && (!idField || !keys.includes(idField))
  );
}

/** Read a contract .jsonl file: header (any corpus shape) + typed rows. */
export function readJsonl<T>(relPath: string, idField?: string): JsonlFile<T> {
  let raw: string;
  try {
    raw = readFileSync(join(extractedRoot(), relPath), "utf8");
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      // empty-by-contract file (e.g. endings relink launch member)
      return { meta: null, rows: [] };
    }
    throw err;
  }
  const lines = raw.split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return { meta: null, rows: [] };
  let meta: Record<string, unknown> | null = null;
  let start = 0;
  const first = JSON.parse(lines[0]) as Record<string, unknown>;
  if (looksLikeHeader(first, idField)) {
    meta =
      first._meta !== undefined
        ? (first._meta as Record<string, unknown>)
        : first;
    start = 1;
  }
  const rows = lines.slice(start).map((l) => JSON.parse(l) as T);
  // Contract row-count pin: declared count must equal the data-row count.
  const declared = meta && typeof meta.row_count === "number" ? meta.row_count : null;
  if (declared !== null && declared !== rows.length) {
    throw new Error(
      `${relPath}: _meta.row_count=${declared} but ${rows.length} data rows`
    );
  }
  return { meta, rows };
}
