/*
 * SERVER-ONLY readers over content/emit/* — the article registry and the
 * per-article locale admission ledger (content-pipeline spec §3). The page
 * layer NEVER opens an .mdx source or re-derives TOC/counts/links at request
 * time (§2 hard rule): everything here reads the M2 artifacts.
 *
 * Same discipline as contracts.ts: first line is a class-A {"_meta": …}
 * header whose row_count pin throws on drift. The registry is the ONLY
 * hand-off surface — adding a consumer means teaching it this shape, never
 * re-parsing article sources.
 *
 * §8.1 single-gate law enforced HERE at runtime (R-CT4, R-CT3 MED-1): every
 * reader below flows through loadArticles(), which rebuilds each row's
 * locale map FROM article_locales.jsonl and throws on any ledger⇄registry
 * divergence — the mirror never admits by itself.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

/** Repo-authored prose artifacts live under site/content (cwd=site at build). */
export function contentRoot(): string {
  return (
    process.env.MISIDE_CONTENT_ROOT ?? join(process.cwd(), "content")
  );
}

export interface ArticleLocaleCell {
  /** Serving path including the locale prefix (pivot bare). */
  path: string;
  title: string;
  description: string;
  word_count: number;
  /** sha16 of THIS cell's own admitted .mdx at admission time. */
  body_sha16?: string;
  /** Non-pivot cells: pivot sha16 the translation was ADMITTED against. */
  base_sha16?: string;
  toc: Array<{ id: string; text: string; level: number }>;
  /**
   * THIS cell's own embed declarations (R-CT3 HIGH-2): anchors were resolved
   * against this cell's headings at emit, props are this cell's authored
   * strings. The row-level `embeds` stays pivot-only and must never be
   * rendered against a translated body — pivot heading ids do not exist there.
   */
  embeds?: Array<{
    id: string;
    after?: string;
    module: "map-scene" | "entity-cards" | "checklist";
    props: Record<string, unknown>;
  }>;
  body_ref: string;
  stale?: boolean;
}

export interface ArticleEntityRef {
  kind: string;
  id: string;
}

export type ArticleType = "guide" | "game" | "database" | "patch";

export interface ArticleRegistryRow {
  article_id: string;
  type: ArticleType;
  slug: string;
  title_en: string;
  locales: Record<string, ArticleLocaleCell>;
  entities: ArticleEntityRef[];
  entity_row_hashes: Record<string, string>;
  toc: Array<{ id: string; text: string; level: number }>;
  spoiler: "none" | "mild" | "full";
  verified_build_id: string;
  published_at: string;
  updated_at: string;
  status: "published";
  stale: boolean;
  steps: string[];
  embeds: Array<{
    id: string;
    after?: string;
    module: "map-scene" | "entity-cards" | "checklist";
    props: Record<string, unknown>;
  }>;
  body_ref: string;
}

export interface ArticlesMeta {
  schema: string;
  generator: string;
  build_id: string;
  version_label: string;
  row_count: number;
  streams: Record<string, number>;
}

interface JsonlFile<T> {
  meta: Record<string, unknown> | null;
  rows: T[];
}

/**
 * readJsonl twin over content/emit (contracts.ts reads ../extracted; these
 * artifacts live beside the site source). Same _meta.row_count pin-or-throw.
 */
function readEmitJsonl<T>(relPath: string, idField?: string): JsonlFile<T> {
  let raw: string;
  try {
    raw = readFileSync(join(contentRoot(), relPath), "utf8");
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      // no articles yet — the pipeline ships green at zero (stub policy §9)
      return { meta: null, rows: [] };
    }
    throw err;
  }
  const lines = raw.split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return { meta: null, rows: [] };
  const first = JSON.parse(lines[0]) as Record<string, unknown>;
  let meta: Record<string, unknown> | null = null;
  let start = 0;
  if (first && typeof first === "object" && ("_meta" in first || "schema" in first)) {
    meta = (first._meta as Record<string, unknown>) ?? first;
    start = 1;
  }
  const rows = lines
    .slice(start)
    .map((l) => JSON.parse(l) as T)
    .filter((r) => r === null || typeof r !== "object" || (idField ? idField in (r as object) : true));
  const declared =
    meta && typeof meta.row_count === "number" ? meta.row_count : null;
  if (declared !== null && declared !== rows.length) {
    throw new Error(
      `${relPath}: _meta.row_count=${declared} but ${rows.length} data rows`
    );
  }
  return { meta, rows };
}

interface LedgerCellRow {
  cell: string;
  article_id: string;
  locale: string;
  path: string;
  stale?: boolean;
}

interface LoadedArticles {
  meta: ArticlesMeta | null;
  /** Registry rows with `locales` rebuilt FROM the admission ledger. */
  rows: ArticleRegistryRow[];
  /** Normalized ledger cells — the §8.1 authoritative admission set. */
  ledgerCells: Array<{
    cell: string;
    article_id: string;
    locale: string;
    path: string;
    stale: boolean;
  }>;
}

// keyed by content root so test lanes can point MISIDE_CONTENT_ROOT at a
// fixture tree without polluting the real tree's cache entry
const cacheByRoot = new Map<string, LoadedArticles>();

/**
 * Load registry + ledger and enforce the §8.1 single-gate law at RUNTIME
 * (R-CT3 MED-1): a locale cell is admitted IFF the ledger carries
 * `<article_id>@<locale>`. The registry mirror still supplies payload
 * columns (toc / body_ref / hashes) but never admits by itself — deleting
 * or corrupting article_locales.jsonl now changes what serves, loudly.
 */
function loadArticles(): LoadedArticles {
  const root = contentRoot();
  const cached = cacheByRoot.get(root);
  if (cached) return cached;

  const registry = readEmitJsonl<ArticleRegistryRow>("emit/articles.jsonl", "article_id");
  const ledger = readEmitJsonl<LedgerCellRow>("emit/article_locales.jsonl", "cell");
  const ledgerCells = ledger.rows
    .filter((r): r is LedgerCellRow => Boolean(r?.cell))
    .map((r) => ({ ...r, stale: r.stale === true }));
  const registryRows = registry.rows.filter((r) => Boolean(r?.article_id));

  // the pair is written in one emit loop; half a pair is corruption
  const registryPresent = registry.meta !== null;
  const ledgerPresent = ledger.meta !== null;
  if (registryPresent !== ledgerPresent) {
    throw new Error(
      `emit artifacts diverge: articles.jsonl ${registryPresent ? "present" : "MISSING"} while article_locales.jsonl ${ledgerPresent ? "present" : "MISSING"} — the ledger is the §8.1 admission gate; rerun scripts/build-content.mjs`
    );
  }

  if (registryPresent) {
    const cellsByArticle = new Map<string, string[]>();
    for (const c of ledgerCells) {
      const list = cellsByArticle.get(c.article_id) ?? [];
      list.push(c.locale);
      cellsByArticle.set(c.article_id, list);
    }
    const registryIds = new Set(registryRows.map((r) => r.article_id));
    const problems: string[] = [];
    for (const [articleId] of cellsByArticle) {
      if (!registryIds.has(articleId)) problems.push(`${articleId} ledger-only`);
    }
    for (const row of registryRows) {
      const admitted = new Set(cellsByArticle.get(row.article_id) ?? []);
      const mirror = Object.keys(row.locales ?? {});
      problems.push(
        ...mirror.filter((code) => !admitted.has(code)).map((code) => `${row.article_id}@${code} registry-only`),
        ...[...admitted].filter((code) => row.locales?.[code] === undefined).map((code) => `${row.article_id}@${code} ledger-only`)
      );
    }
    if (problems.length > 0) {
      throw new Error(
        `emit/article_locales.jsonl ⇄ articles.jsonl locale-cell divergence (${problems.join("; ")}) — the ledger is authoritative for admission (§8.1); rerun scripts/build-content.mjs`
      );
    }
  }

  // rebuild each row's locales FROM the ledger cells (mirror supplies columns)
  const gatedRows = registryRows.map((row) => {
    const locales: Record<string, ArticleLocaleCell> = {};
    for (const c of ledgerCells) {
      if (c.article_id !== row.article_id) continue;
      const mirrorCell = row.locales[c.locale];
      if (!mirrorCell) continue; // unreachable post-check above
      locales[c.locale] = mirrorCell;
    }
    return { ...row, locales };
  });

  const loaded: LoadedArticles = {
    meta: (registry.meta as unknown as ArticlesMeta) ?? null,
    rows: gatedRows,
    ledgerCells,
  };
  cacheByRoot.set(root, loaded);
  return loaded;
}

/** Full published-article registry (empty when nothing is published yet). */
export function articlesMetaAndRows(): { meta: ArticlesMeta | null; rows: ArticleRegistryRow[] } {
  const loaded = loadArticles();
  return { meta: loaded.meta, rows: loaded.rows };
}

export function publishedArticles(): ArticleRegistryRow[] {
  return articlesMetaAndRows().rows;
}

export function articlesBuildStamp(): { build_id: string; version_label: string } | null {
  const meta = articlesMetaAndRows().meta;
  if (!meta) return null;
  return { build_id: String(meta.build_id ?? ""), version_label: String(meta.version_label ?? "") };
}

/** One article by URL slug within a section (guides | news). */
export function articleBySlug(
  section: "guides" | "news",
  slug: string
): ArticleRegistryRow | undefined {
  return publishedArticles().find((r) =>
    section === "guides" ? r.type === "guide" && r.slug === slug : r.type !== "guide" && r.slug === slug
  );
}

/** Published rows of one typed stream (game | database | patch | guide). */
export function streamRows(type: ArticleType): ArticleRegistryRow[] {
  return publishedArticles().filter((r) => r.type === type);
}

/**
 * The M5 admission ledger — the SINGLE gate for route admission, sitemap
 * partitions and hreflang clusters (§8.1). Cells mirror the registry's
 * per-locale hashes; the ledger copy is authoritative — and since R-CT4 it
 * is enforced at RUNTIME too: `loadArticles()` rebuilds every row's locale
 * map from these cells and refuses divergent artifacts outright.
 */
export function articleLocaleCells(): Array<{
  cell: string;
  article_id: string;
  locale: string;
  path: string;
  stale: boolean;
}> {
  // normalize the optional emitted column to the declared boolean contract
  // (undefined → false); truthy semantics for consumers are unchanged
  return loadArticles().ledgerCells;
}

/** Admitted article paths for ONE section + locale (sitemap/partition gate). */
export function admittedArticlePaths(
  section: "guides" | "news",
  localeCode: string
): string[] {
  const rows = publishedArticles()
    .filter((r) => (section === "guides" ? r.type === "guide" : r.type !== "guide"))
    .filter((r) => Boolean(r.locales[localeCode]));
  return rows.map((r) => r.locales[localeCode].path);
}

/** Locale codes admitting ANY article of a section (index-page admission). */
export function admittedSectionLocales(section: "guides" | "news"): string[] {
  const codes = new Set<string>();
  for (const r of publishedArticles()) {
    if (section === "guides" ? r.type !== "guide" : r.type === "guide") continue;
    for (const code of Object.keys(r.locales)) codes.add(code);
  }
  return [...codes].sort();
}

/** Reverse-link source: published articles referencing one routed entity. */
export function articlesReferencing(
  kind: string,
  id: string
): ArticleRegistryRow[] {
  return publishedArticles().filter((r) =>
    r.entities.some((e) => e.kind === kind && e.id === id)
  );
}

/** Compiled body for one locale cell — lazy, page-scoped, never bundled. */
export function articleBody(article: ArticleRegistryRow, localeCode: string): string | null {
  const ref = article.locales[localeCode]?.body_ref ?? article.body_ref;
  if (!ref) return null;
  try {
    return readFileSync(join(contentRoot(), "emit", "bodies", ref), "utf8");
  } catch {
    return null;
  }
}
