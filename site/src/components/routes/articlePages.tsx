import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { getChrome } from "@/i18n/request";
import { getLocale, LOCALES } from "@/i18n/locales";
import { findRow, kindIds, ENTITY_KINDS } from "@/data/contracts";
import {
  admittedSectionLocales,
  articleBody,
  articleBySlug,
  articlesBuildStamp,
  publishedArticles,
} from "@/data/articles";
import { displayName, indexArtFor } from "./entityView";
import { entityHref } from "@/lib/routes";
import { buildAlternates } from "@/lib/hreflang";
import {
  ArticleIndexRoute,
  type ArticleIndexCard,
  type NewsStreamView,
} from "./ArticleIndexRoute";
import {
  ArticleRoute,
  type PreparedEmbed,
  type RelatedEntityCard,
} from "./ArticleRoute";

/*
 * M3/M4 page-content factories shared by BOTH trees (content-pipeline §2):
 * the (pivot)/[locale] wrapper files stay thin and carry zero route logic.
 * Everything reads the M2 registry + admission ledger — never article
 * sources, never request-time derivation (§2 hard rule).
 */

const SECTION_TITLE_KEY: Record<string, string> = {
  guides: "nav.guides",
  news: "nav.news",
};

export const CONTENT_SECTIONS = ["guides", "news"] as const;
export type ContentSection = (typeof CONTENT_SECTIONS)[number];

function chromeFor(localeCode: string) {
  const def = getLocale(localeCode);
  if (!def) notFound();
  return { def, chrome: getChrome(def) as unknown as Record<string, string> };
}

function buildStamp(): string {
  const stamp = articlesBuildStamp();
  return stamp ? `${stamp.build_id} (${stamp.version_label})` : "";
}

/* ------------------------------------------------------------------ */
/* Index pages — /guides hub grid · /news one-hub-three-streams        */
/* ------------------------------------------------------------------ */

export function buildArticleIndexMetadata(
  section: ContentSection,
  localeCode: string
): Metadata {
  const { def, chrome } = chromeFor(localeCode);
  // hreflang cluster == ledger membership for this section (§7.3)
  const cluster = admittedSectionLocales(section);
  if (!cluster.includes(def.code)) cluster.push(def.code);
  return {
    title: chrome[SECTION_TITLE_KEY[section]],
    alternates: {
      canonical: `${def.prefix}/${section}`,
      languages: buildAlternates(`/${section}`, cluster),
    },
  };
}

export function ArticleIndexContent({
  section,
  localeCode,
}: {
  section: ContentSection;
  localeCode: string;
}) {
  const { def, chrome } = chromeFor(localeCode);
  const rows = publishedArticles().filter((r) =>
    section === "guides" ? r.type === "guide" : r.type !== "guide"
  );

  if (section === "news") {
    const streams: NewsStreamView[] = (
      ["game", "database", "patch"] as const
    ).map((type) => ({
      type,
      label: chrome[`news.stream.${type}`],
      items: rows
        .filter((r) => r.type === type && r.locales[def.code])
        .map((r) => ({
          href: r.locales[def.code].path,
          title: r.locales[def.code].title,
          description: r.locales[def.code].description,
          date: r.published_at,
        })),
    }));
    // zero-item streams omit themselves inside the hub (§7.4)
    return (
      <ArticleIndexRoute
        section="news"
        title={chrome["nav.news"]}
        streams={streams}
        chrome={chrome}
        localePrefix={def.prefix}
      />
    );
  }

  const cards: ArticleIndexCard[] = rows
    .filter((r) => r.locales[def.code])
    .map((r) => ({
      href: r.locales[def.code].path,
      title: r.locales[def.code].title,
      description: r.locales[def.code].description,
      count: `words:${r.locales[def.code].word_count}`,
    }));
  return (
    <ArticleIndexRoute
      section="guides"
      title={chrome["nav.guides"]}
      cards={cards}
      chrome={chrome}
      localePrefix={def.prefix}
    />
  );
}

/* ------------------------------------------------------------------ */
/* Detail pages — admission gate = the ledger cell (C2, zero exceptions) */
/* ------------------------------------------------------------------ */

export function resolveArticleCell(
  section: ContentSection,
  slug: string,
  localeCode: string
) {
  const row = articleBySlug(section, slug);
  if (!row) notFound(); // unknown slug → 404, matching AC S6
  const cell = row.locales[localeCode];
  if (!cell) notFound(); // non-admitted locale → no URL exists (omit-fallback)
  return { row, cell };
}

export function buildArticleMetadata(
  section: ContentSection,
  slug: string,
  localeCode: string
): Metadata {
  const def = getLocale(localeCode);
  if (!def) notFound();
  const { row, cell } = resolveArticleCell(section, slug, def.code);
  return {
    // unique localized title/description FROM THAT LOCALE'S authored strings
    title: cell.title,
    description: cell.description,
    alternates: {
      // self-canonical carries the serving prefix exactly like the URL
      canonical: `${def.prefix}/${section}/${slug}`,
      // cluster == ledger membership (registry mirrors the ledger at emit)
      languages: buildAlternates(`/${section}/${slug}`, Object.keys(row.locales)),
    },
  };
}

/** Related-entity cards over the article's declared entities[] (kit rules). */
function relatedCardsFor(
  entities: Array<{ kind: string; id: string }>,
  localeCode: string
): RelatedEntityCard[] {
  const prefix = getLocale(localeCode)?.prefix ?? "";
  const cards: RelatedEntityCard[] = [];
  for (const ref of entities) {
    if (!ENTITY_KINDS[ref.kind]) continue;
    const row = findRow(ref.kind, ref.id);
    if (!row) continue;
    cards.push({
      href: entityHref(prefix, ref.kind, ref.id),
      title: displayName(ref.kind, row as Record<string, unknown>, localeCode),
      img: indexArtFor(ref.kind, row as unknown as Record<string, unknown>, localeCode),
    });
  }
  return cards;
}

/**
 * Pre-materialize declared embeds against the closed §5 module map. The page
 * layer validates nothing here — emit already validated modules, props and
 * anchors; unknown anchors degrade to end-of-body in ArticleRoute.
 */
function prepareEmbeds(
  embeds: Array<{
    id: string;
    after?: string;
    module: "map-scene" | "entity-cards" | "checklist";
    props: Record<string, unknown>;
  }>,
  entities: Array<{ kind: string; id: string }>,
  localeCode: string
): PreparedEmbed[] {
  return embeds.map((emb) => {
    if (emb.module === "checklist") {
      return {
        kind: "checklist",
        id: emb.id,
        after: emb.after,
        title: typeof emb.props.title === "string" ? emb.props.title : undefined,
        items: (Array.isArray(emb.props.items) ? emb.props.items : []).map(
          (it) => ({
            text: String(it?.text ?? ""),
            keys: Array.isArray(it?.keys) ? it.keys.map(String) : undefined,
            danger: Boolean(it?.danger),
          })
        ),
      };
    }
    if (emb.module === "entity-cards") {
      return {
        kind: "entity-cards",
        id: emb.id,
        after: emb.after,
        title: typeof emb.props.title === "string" ? emb.props.title : undefined,
        cards: relatedCardsFor(entities, localeCode),
      };
    }
    return {
      kind: "map-scene",
      id: emb.id,
      after: emb.after,
      sceneId: String(emb.props.scene_id ?? ""),
    };
  });
}

export function ArticleContent({
  section,
  slug,
  localeCode,
}: {
  section: ContentSection;
  slug: string;
  localeCode: string;
}) {
  const { def, chrome } = chromeFor(localeCode);
  const { row, cell } = resolveArticleCell(section, slug, def.code);
  const html = articleBody(row, def.code);
  if (!html) notFound(); // registry row without its compiled body is a defect
  return (
    <ArticleRoute
      section={section}
      slug={slug}
      row={row}
      cell={cell}
      html={html}
      relatedCards={relatedCardsFor(row.entities, def.code)}
      embeds={prepareEmbeds(row.embeds, row.entities, def.code)}
      chrome={chrome}
      localeCode={def.code}
      localePrefix={def.prefix}
      buildStamp={buildStamp()}
    />
  );
}

/* ------------------------------------------------------------------ */
/* generateStaticParams sources — registry/ledger ONLY (never a dir     */
/* listing), so route output == admitted cells in FULL diff (AC C2).    */
/* ------------------------------------------------------------------ */

export function articleParamsPivot(section: ContentSection): Array<Record<string, string>> {
  const param = section === "guides" ? "guide_slug" : "news_slug";
  return publishedArticles()
    .filter((r) =>
      section === "guides" ? r.type === "guide" : r.type !== "guide"
    )
    .filter((r) => Boolean(r.locales.en))
    .map((r) => ({ [param]: r.slug }));
}

export function articleParamsByLocale(
  section: ContentSection
): Array<Record<string, string>> {
  const param = section === "guides" ? "guide_slug" : "news_slug";
  const out: Array<Record<string, string>> = [];
  for (const def of LOCALES) {
    if (def.prefix === "") continue; // pivot serves bare paths only
    for (const r of publishedArticles()) {
      if (section === "guides" ? r.type !== "guide" : r.type === "guide") continue;
      if (!r.locales[def.code]) continue;
      out.push({ locale: def.code, [param]: r.slug });
    }
  }
  return out;
}

/** Guard used by tests: routed-kind totality still holds for declared refs. */
export function declaredEntityIdsResolvable(entities: Array<{ kind: string; id: string }>): boolean {
  return entities.every((e) => ENTITY_KINDS[e.kind] && kindIds(e.kind).includes(e.id));
}
