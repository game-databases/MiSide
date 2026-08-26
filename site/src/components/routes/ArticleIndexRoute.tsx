import Link from "next/link";

import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { CartridgeCard } from "@/components/kit/CartridgeCard";
import { GradientPill } from "@/components/kit/GradientPill";
import type { Chrome } from "@/i18n/request";
import { asRoute } from "@/lib/utils";

/*
 * M3/M4 section index factory (content-pipeline spec §6.1/§7.1):
 *  • /guides  — grid of guide cards (cartridge-card language, honest wells
 *    where no art exists);
 *  • /news    — ONE hub, three typed streams; stream-filtered views are chip
 *    states anchored in place, NOT separate URL sections (facet combinations
 *    create no URLs). Empty streams omit themselves entirely (§7.4) — no
 *    captions, no placeholder cards.
 *
 * Rows arrive pre-resolved for THIS locale from the M2 registry — this
 * component never opens article sources.
 */

export interface ArticleIndexCard {
  href: string;
  title: string;
  description: string;
  /** Reader-facing chip text (word count / date). */
  count?: string;
}

export interface NewsStreamView {
  type: "game" | "database" | "patch";
  label: string;
  items: Array<{ href: string; title: string; description: string; date: string }>;
}

export function ArticleIndexRoute({
  section,
  title,
  cards,
  streams,
  chrome,
  localePrefix,
}: {
  section: "guides" | "news";
  title: string;
  /** Guides grid (empty when nothing is published). */
  cards?: ArticleIndexCard[];
  /** News hub streams (empty members omitted by the caller, §7.4). */
  streams?: NewsStreamView[];
  chrome: Chrome;
  localePrefix: string;
}) {
  const homeLabel = chrome["breadcrumb.home"];
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={[section]}
        labels={{ [section]: title }}
        homeLabel={homeLabel}
      />
      <GradientPill className="w-fit">{title}</GradientPill>

      {section === "guides" ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {(cards ?? []).map((c) => (
            <CartridgeCard
              key={c.href}
              href={c.href}
              title={c.title}
              count={c.count}
            >
              <span className="mt-1 line-clamp-2 block text-xs font-normal text-muted-foreground">
                {c.description}
              </span>
            </CartridgeCard>
          ))}
        </div>
      ) : (
        <NewsHub streams={streams ?? []} />
      )}
    </div>
  );
}

function NewsHub({ streams }: { streams: NewsStreamView[] }) {
  const live = streams.filter((s) => s.items.length > 0);
  if (live.length === 0) return null; // honest empty: omission, never a caption
  return (
    <div className="flex flex-col gap-8">
      {/* type chips — anchor states inside the one hub URL */}
      <nav className="flex flex-wrap gap-2" aria-label="Streams">
        {live.map((s) => (
          <Link
            key={s.type}
            href={asRoute(`#${s.type}`)}
            className="inline-flex min-h-11 items-center rounded-full border border-border px-4 py-1.5 font-lcd text-xs uppercase tracking-wide hover:bg-accent"
          >
            {s.label}
            <span className="ml-2 text-muted-foreground">{s.items.length}</span>
          </Link>
        ))}
      </nav>
      {live.map((s) => (
        <section key={s.type} id={s.type} className="flex scroll-mt-24 flex-col gap-3">
          <h2 className="flex items-center gap-3">
            <span className="font-lcd text-sm uppercase tracking-wide">{s.label}</span>
            <span className="h-px flex-1 bg-border" />
          </h2>
          <ul className="flex flex-col gap-2">
            {s.items.map((it) => (
              <li key={it.href}>
                <Link
                  href={asRoute(it.href)}
                  className="flex min-h-11 flex-col gap-0.5 rounded-md border border-border bg-card px-4 py-3 hover:bg-accent"
                >
                  <span className="flex flex-wrap items-baseline gap-x-3">
                    <span className="text-sm font-bold underline-offset-4 group-hover:underline">
                      {it.title}
                    </span>
                    <span className="font-lcd text-xs text-muted-foreground">{it.date}</span>
                  </span>
                  <span className="line-clamp-2 block text-xs text-muted-foreground">
                    {it.description}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
