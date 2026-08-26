import Link from "next/link";

import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { CartridgeCard } from "@/components/kit/CartridgeCard";
import { GradientPill } from "@/components/kit/GradientPill";
import { KeycapKbd } from "@/components/kit/KeycapKbd";
import { VoidWell } from "@/components/kit/VoidWell";
import type { Chrome } from "@/i18n/request";
import { SITE_ORIGIN } from "@/lib/siteConfig";
import { asRoute } from "@/lib/utils";
import type { ArticleLocaleCell, ArticleRegistryRow } from "@/data/articles";

/*
 * M3/M4 article detail factory (content-pipeline spec §6.2): answer-shaped
 * lead block → TOC (registry-sourced, anchor-linked) → compiled body with
 * declared §5 embed slots → related-entities row → reserved comments slot
 * (renders nothing until the UGC piece lands). Guides carry HowTo JSON-LD
 * only when steps[] is populated; news wears NewsArticle JSON-LD (M4 only).
 *
 * The body HTML arrives COMPILED from content/emit/bodies (escape-first law
 * enforced at emit, C14) — this component never parses markdown and never
 * opens an .mdx source. Embed modules arrive PRE-MATERIALIZED server-side
 * (articlePages.tsx) against the closed §5 module map.
 */

export interface RelatedEntityCard {
  href: string;
  title: string;
  img?: string;
}

export type PreparedEmbed =
  | {
      kind: "entity-cards";
      id: string;
      after?: string;
      title?: string;
      cards: RelatedEntityCard[];
    }
  | {
      kind: "checklist";
      id: string;
      after?: string;
      title?: string;
      items: Array<{ text: string; keys?: string[]; danger?: boolean }>;
    }
  | { kind: "map-scene"; id: string; after?: string; sceneId: string };

export interface ArticleDetailView {
  section: "guides" | "news";
  slug: string;
  cell: ArticleLocaleCell;
  row: ArticleRegistryRow;
  /** Compiled body HTML for THIS locale cell (validated at emit, C14). */
  html: string;
  relatedCards: RelatedEntityCard[];
  embeds: PreparedEmbed[];
  chrome: Chrome;
  localeCode: string;
  localePrefix: string;
  /** User-facing provenance stamp — narrowest truthful granularity (D2). */
  buildStamp: string;
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Split the compiled HTML around embed anchors so declared modules render
 * inside the flow after their heading. Anchors were validated at emit time
 * against this cell's own TOC; an unknown anchor degrades to end-of-body.
 */
function interleave(html: string, embeds: PreparedEmbed[]): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let rest = html;
  const anchored = embeds.filter((e) => e.after);
  const tail = embeds.filter((e) => !e.after);
  let guard = 0;
  while (anchored.length > 0 && guard++ < 100) {
    let bestIdx = -1;
    let bestEnd = -1;
    let best: PreparedEmbed | null = null;
    for (const emb of anchored) {
      const re = new RegExp(
        `<h[1-6] id="${escapeRegExp(emb.after as string)}"[^>]*>[\\s\\S]*?</h[1-6]>`,
        "i"
      );
      const m = re.exec(rest);
      if (!m) continue;
      if (bestIdx === -1 || m.index < bestIdx) {
        bestIdx = m.index;
        bestEnd = m.index + m[0].length;
        best = emb;
      }
    }
    if (!best) break;
    nodes.push(<BodyChunk key={`c${nodes.length}`} html={rest.slice(0, bestEnd)} />);
    nodes.push(<EmbedSlot key={`e:${best.id}`} embed={best} />);
    rest = rest.slice(bestEnd);
    anchored.splice(anchored.indexOf(best), 1);
  }
  nodes.push(<BodyChunk key={`c${nodes.length}`} html={rest} />);
  for (const emb of tail) {
    nodes.push(<EmbedSlot key={`e:${emb.id}`} embed={emb} />);
  }
  return nodes;
}

function BodyChunk({ html }: { html: string }) {
  if (html.trim() === "") return null;
  return (
    <div
      dangerouslySetInnerHTML={{ __html: html }}
      className="article-body flex flex-col gap-4 text-[15px] leading-relaxed [&_a]:font-bold [&_a]:underline [&_a]:underline-offset-4 [&_code]:rounded [&_code]:bg-secondary [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-lcd [&_code]:text-xs [&_h2]:mt-4 [&_h2]:text-xl [&_h2]:font-bold [&_h2]:uppercase [&_h2]:tracking-wide [&_h3]:mt-3 [&_h3]:text-lg [&_h3]:font-bold [&_li]:ml-5 [&_ol_li]:list-decimal [&_table]:w-full [&_table]:text-sm [&_td]:border [&_td]:border-border [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:border-border [&_th]:px-2 [&_th]:py-1 [&_ul_li]:list-disc"
    />
  );
}

/** Closed §5 module map renderer — OUR components only. */
function EmbedSlot({ embed }: { embed: PreparedEmbed }) {
  if (embed.kind === "checklist") {
    return (
      <div className="flex flex-col gap-2">
        {embed.title && (
          <span className="font-lcd text-xs uppercase tracking-wide text-muted-foreground">
            {embed.title}
          </span>
        )}
        <ol className="flex flex-col gap-2">
          {embed.items.map((it, i) => (
            <li
              key={i}
              className="flex min-h-11 flex-wrap items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm"
              style={
                it.danger
                  ? { borderColor: "var(--ms-danger)" }
                  : undefined
              }
            >
              <span className="font-lcd text-xs text-muted-foreground">{i + 1}</span>
              <span className="font-bold">{it.text}</span>
              {/* red is SEMANTIC: this step loses you something (§6.3) */}
              {it.danger && (
                <span
                  aria-hidden
                  className="inline-flex items-center rounded-full px-2 py-0.5 font-lcd text-xs text-primary-foreground"
                  style={{ background: "var(--ms-danger)" }}
                >
                  !
                </span>
              )}
              {it.keys?.map((k) => (
                <KeycapKbd key={k}>{k}</KeycapKbd>
              ))}
            </li>
          ))}
        </ol>
      </div>
    );
  }
  if (embed.kind === "entity-cards") {
    return (
      <div className="flex flex-col gap-3">
        {embed.title && (
          <span className="font-lcd text-xs uppercase tracking-wide text-muted-foreground">
            {embed.title}
          </span>
        )}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {embed.cards.map((c) => (
            <CartridgeCard
              key={c.href}
              href={c.href}
              title={c.title}
              img={c.img}
              imgAlt={c.img ? c.title : undefined}
            />
          ))}
        </div>
      </div>
    );
  }
  // map-scene: the LANE-B island slot. ⛓ LANE-B is still open, so the slot
  // renders VoidWell honest-empty — never a substitute (spec §5). Declared
  // either way so no guide is rewritten when the island lands.
  return (
    <VoidWell
      className="aspect-[16/9] w-full"
      aria-label={embed.sceneId || embed.id}
    />
  );
}

export function ArticleRoute(view: ArticleDetailView) {
  const { row, cell, chrome, localePrefix } = view;
  const segment = view.section;
  const isGuide = row.type === "guide";

  // HowTo ONLY when steps[] is populated and honest (§6.2); expect no rich result.
  const howToJsonld =
    isGuide && row.steps.length > 0
      ? {
          "@context": "https://schema.org",
          "@type": "HowTo",
          name: cell.title,
          description: cell.description,
          step: row.steps.map((text, i) => ({
            "@type": "HowToStep",
            position: i + 1,
            text,
          })),
        }
      : null;

  const newsJsonld =
    !isGuide &&
    ({
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      headline: cell.title,
      description: cell.description,
      datePublished: row.published_at,
      dateModified: row.updated_at,
      inLanguage: view.localeCode,
      mainEntityOfPage: `${SITE_ORIGIN}${cell.path}`,
      // machine-plane identity rides the JSON-LD layer only (§7.2)
      about: row.entities.map((e) => `${e.kind}:${e.id}`),
    } satisfies Record<string, unknown>);

  return (
    <article className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={[segment, view.slug]}
        labels={{
          [segment]: chrome[isGuide ? "nav.guides" : "nav.news"],
          [view.slug]: cell.title,
        }}
        homeLabel={chrome["breadcrumb.home"]}
      />
      <header className="flex flex-col gap-3">
        <GradientPill className="w-fit">
          {chrome[isGuide ? "nav.guides" : "nav.news"]}
        </GradientPill>
        <h1 className="max-w-3xl text-3xl font-bold uppercase tracking-wide">
          {cell.title}
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          {cell.description}
        </p>
        {/* user-facing provenance stamp — narrowest truthful granularity (D2) */}
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 font-lcd text-xs text-muted-foreground">
          <span>
            {chrome["footer.buildLabel"]} {view.buildStamp}
          </span>
          <span>{row.published_at}</span>
          {row.updated_at !== row.published_at && (
            <span>
              {chrome["article.updated"]} {row.updated_at}
            </span>
          )}
        </p>
      </header>

      {isGuide && cell.toc.length > 1 && (
        <nav
          aria-label={chrome["article.toc"]}
          className="flex w-fit flex-col gap-1 rounded-md border border-border p-4"
        >
          <span className="mb-1 font-lcd text-xs uppercase tracking-wide text-muted-foreground">
            {chrome["article.toc"]}
          </span>
          {cell.toc.map((h) => (
            <Link
              key={h.id}
              href={asRoute(`${cell.path}#${h.id}`)}
              className="text-sm hover:underline"
              style={{ paddingInlineStart: `${(h.level - 2) * 0.75}rem` }}
            >
              {h.text}
            </Link>
          ))}
        </nav>
      )}

      <div className="flex max-w-3xl flex-col gap-5">
        {interleave(view.html, view.embeds)}

        {view.relatedCards.length > 0 && (
          <section className="mt-4 flex flex-col gap-3">
            <span className="w-fit self-start rounded-full border border-border px-3 py-1 font-lcd text-xs uppercase tracking-wide text-muted-foreground">
              {chrome["article.related"]}
            </span>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {view.relatedCards.map((c) => (
                <CartridgeCard
                  key={c.href}
                  href={c.href}
                  title={c.title}
                  img={c.img}
                  imgAlt={c.img ? c.title : undefined}
                />
              ))}
            </div>
          </section>
        )}

        {/* comments slot — reserved for the UGC piece; renders nothing */}
      </div>

      {howToJsonld && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(howToJsonld) }}
        />
      )}
      {newsJsonld && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(newsJsonld) }}
        />
      )}
    </article>
  );
}
