/*
 * ONE matching function, imported by server AND browser (spec §6).
 * What matches cannot depend on which side answered.
 *
 * Server: builds rows from contract readers (SSR fallback + emitted-index
 * generation in scripts/emit-artifacts.mjs via the same row schema).
 * Browser: loads the emitted public/search/<locale>.idx.json and runs the
 * identical function. Indexes are disposable derived artifacts (FRAMEWORK §2.1).
 */
import MiniSearch from "minisearch";

export interface SearchRow {
  /**
   * Stable entity id, kind-namespaced in emitted indexes
   * (`<kind>:<contract-id>`) — MiniSearch requires globally-unique document
   * ids and raw columns collide across kinds ("level4" is both a scene_id
   * and a dialogue carrier).
   */
  id: string;
  /** URL kind segment (mita, cartridges, …). */
  kind: string;
  title: string;
  text?: string;
  /** Locale-resolved page path (pivot-bare or prefixed). */
  url: string;
}

export interface SearchHit {
  id: string;
  kind: string;
  title: string;
  url: string;
  score: number;
}

/** Reactive-input law: nothing matches before two typed characters (DR-2026-08-22-search-is-not-a-page ¶4). */
export const MIN_QUERY_LENGTH = 2;

/**
 * Render cap (VC-2 fix #4): the old hard 20 silently hid whole matching
 * kinds (32 of 52 "mita" rows invisible). The cap now KIND-BALANCES before
 * truncating and the field renders the remainder as a "+N" chip, so no
 * matching kind is invisible.
 */
export const MAX_VISIBLE_ROWS = 60;

export function createSearchIndex(rows: SearchRow[]): MiniSearch<SearchRow> {
  return new MiniSearch<SearchRow>({
    fields: ["title", "text"],
    storeFields: ["id", "kind", "title", "url"],
    searchOptions: {
      prefix: true,
      fuzzy: 0.2,
      boost: { title: 3 },
    },
  });
}

export function indexAll(index: MiniSearch<SearchRow>, rows: SearchRow[]): void {
  index.addAll(rows);
}

interface RawHit {
  id: string | number;
  score: number;
  kind?: string;
  title?: string;
  url?: string;
}

function matchHits(
  index: MiniSearch<SearchRow>,
  rawQuery: string,
  opts?: { kind?: string }
): RawHit[] {
  const q = rawQuery.trim();
  if (q.length < MIN_QUERY_LENGTH) return [];
  let hits = index.search(q) as RawHit[];
  if (opts?.kind && opts.kind !== "all") {
    hits = hits.filter((h) => h.kind === opts.kind);
  }
  return hits;
}

/**
 * Kind-balanced truncation: score order WITHIN a kind is kept, but kinds
 * take rounds so one dense kind cannot crowd every other kind out of the
 * visible rows. Under the cap the pure score order passes through untouched.
 */
function interleaveByKind<T extends { kind?: string }>(hits: T[], limit: number): T[] {
  if (limit >= hits.length) return hits;
  const queues = new Map<string, T[]>();
  for (const h of hits) {
    const k = String(h.kind ?? "");
    const queue = queues.get(k);
    if (queue) queue.push(h);
    else queues.set(k, [h]);
  }
  const out: T[] = [];
  let progressed = true;
  while (out.length < limit && progressed) {
    progressed = false;
    for (const queue of queues.values()) {
      if (out.length >= limit) break;
      const next = queue.shift();
      if (next !== undefined) {
        out.push(next);
        progressed = true;
      }
    }
  }
  return out;
}

/**
 * The matching function. Same input rows + query → same hits on both sides.
 * Faceting by entity type rides the same function and stays client-local —
 * facet combinations create no URLs (spec §6).
 */
export function searchRows(
  index: MiniSearch<SearchRow>,
  rawQuery: string,
  opts?: { kind?: string; limit?: number }
): SearchHit[] {
  const hits = matchHits(index, rawQuery, opts);
  return interleaveByKind(hits, opts?.limit ?? MAX_VISIBLE_ROWS).map((h) => ({
    id: String(h.id),
    kind: String(h.kind ?? ""),
    title: String(h.title ?? ""),
    url: String(h.url ?? "/"),
    score: h.score,
  }));
}

/**
 * Pre-truncation match count — feeds the "+N more" chip so the cap never
 * reads as "these are all". Same matching path as searchRows.
 */
export function countSearchHits(
  index: MiniSearch<SearchRow>,
  rawQuery: string,
  opts?: { kind?: string }
): number {
  return matchHits(index, rawQuery, opts).length;
}
