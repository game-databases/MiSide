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

let cached: {
  meta: ArticlesMeta | null;
  rows: ArticleRegistryRow[];
} | null = null;

/** Full published-article registry (empty when nothing is published yet). */
export function articlesMetaAndRows(): { meta: ArticlesMeta | null; rows: ArticleRegistryRow[] } {
  if (!cached) {
    const { meta, rows } = readEmitJsonl<ArticleRegistryRow>(
      "emit/articles.jsonl",
      "article_id"
    );
    cached = {
      meta: (meta as unknown as ArticlesMeta) ?? null,
      rows: rows.filter((r) => Boolean(r?.article_id)),
    };
  }
  return cached;
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
 * per-locale hashes; the ledger copy is authoritative.
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
  return readEmitJsonl<{
    cell: string;
    article_id: string;
    locale: string;
    path: string;
    stale?: boolean;
  }>("emit/article_locales.jsonl", "cell")
    .rows.filter((r) => Boolean(r?.cell))
    .map((r) => ({ ...r, stale: r.stale === true }));
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
