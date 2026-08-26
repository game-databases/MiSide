import * as React from "react";

import { cn } from "@/lib/utils";
import { crossLocaleRow } from "@/lib/hreflang";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CorruptionHover } from "@/components/kit/CorruptionHover";

/*
 * EntityShell — the FRAMEWORK §2.8 anatomy every entity page composes:
 * sticky in-fiction card → share rail → H1 + quotable answer block (feeds
 * meta description) → cross-locale link row → conditional tabs (present only
 * when the entity has that data; inactive panels hidden in served HTML,
 * never client-only). Mita-keyed colour identity: sets data-character and
 * re-keys --ms-accent-local from personages palette floats — a shared grey
 * card with a swapped portrait is a fail.
 *
 * The cross-locale row keeps EVERY ledger locale as a real <a href> (the
 * localization-architecture §2 contract) but renders COLLAPSED under one
 * quiet chip — a 30-pill wall read as ontology noise (VC-1); <details> is
 * plain HTML, so the links stay crawlable with zero JS. The visible buildId
 * stamp lives in the sitewide footer; the shell does not duplicate it.
 */
export function EntityShell(props: {
  locale: string;
  kind: string;
  id: string;
  /** Resolved display name for THIS locale (never another locale's text). */
  name: string;
  /** Quotable answer block: data-generated sentences; same builder feeds meta description. */
  quotable?: React.ReactNode;
  /** Sticky card content slot (portrait, key stats). */
  card?: React.ReactNode;
  /** Share rail slot (card screenshot + URL watermark) — later piece wires it. */
  shareRail?: React.ReactNode;
  /** Conditional modules/tabs; render ONLY data-bearing ones. */
  tabs?: Array<{ id: string; label: React.ReactNode; panel: React.ReactNode }>;
  /** Mita-keyed local accent hex (tier-3 token), when the row owns a palette. */
  accentLocal?: string;
  accentSoftLocal?: string;
  /** The client's own broken surface (present-but-unreachable stubs): horror register as STATE. */
  compromised?: boolean;
  /** Ledger-admitted locales for this page — drives the cross-locale row. */
  availableLocales: readonly string[];
  className?: string;
}) {
  const {
    locale,
    kind,
    id,
    name,
    quotable,
    card,
    shareRail,
    tabs,
    accentLocal,
    accentSoftLocal,
    compromised = false,
    availableLocales,
    className,
  } = props;

  const localStyle = {
    ...(accentLocal ? { "--ms-accent-local": accentLocal } : {}),
    ...(accentSoftLocal ? { "--ms-accent-local-soft": accentSoftLocal } : {}),
  } as React.CSSProperties;

  return (
    <div
      data-character={accentLocal ? id : undefined}
      style={localStyle}
      className={cn("mx-auto w-full max-w-6xl px-4", className)}
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        {/* sticky in-fiction card */}
        <aside
          data-slot="entity-card"
          className="h-fit overflow-hidden rounded-lg border border-border bg-card shadow-glow-pink lg:sticky lg:top-20"
        >
          {/* colour-is-identity spine — re-keys to this entity's soul */}
          <span
            aria-hidden
            className="block h-1.5 w-full [background-image:var(--ms-accent-gradient)]"
            style={accentLocal ? { backgroundImage: "none", background: accentLocal } : undefined}
          />
          <div className="p-5">{card}</div>
        </aside>

        <div className="flex flex-col gap-5">
          <div className="flex items-start justify-between gap-4">
            {compromised ? (
              <CorruptionHover active className="rounded-md">
                <h1 className="text-3xl font-bold leading-tight">{name}</h1>
              </CorruptionHover>
            ) : (
              <h1 className="text-3xl font-bold leading-tight">{name}</h1>
            )}
            {shareRail /* share rail slot */}
          </div>

          {/* quotable answer block */}
          {quotable !== undefined && (
            <section data-slot="quotable" className="rounded-lg bg-card p-5 text-sm leading-relaxed">
              {quotable}
            </section>
          )}

          {/* cross-locale row — full contract membership, collapsed presentation */}
          <details data-slot="locale-row" className="group w-fit">
            <summary className="inline-block cursor-pointer list-none rounded-full bg-secondary px-3 py-1 font-lcd text-xs uppercase text-secondary-foreground hover:bg-accent [&::-webkit-details-marker]:hidden">
              {locale}
            </summary>
            <ul className="mt-2 flex flex-wrap items-center gap-1.5">
              {crossLocaleRow(locale, kind, id, availableLocales).map((l) => (
                <li key={l.code}>
                  <a
                    href={l.href}
                    hrefLang={l.code}
                    className="inline-block rounded-full bg-secondary px-2.5 py-0.5 font-lcd text-xs text-secondary-foreground hover:bg-accent"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </details>

          {/* conditional tabs — only when the entity has that data; inactive
              panels stay `hidden` in the served HTML */}
          {tabs && tabs.length > 0 && (
            <Tabs defaultValue={tabs[0].id}>
              <TabsList>
                {tabs.map((tb) => (
                  <TabsTrigger key={tb.id} value={tb.id}>
                    {tb.label}
                  </TabsTrigger>
                ))}
              </TabsList>
              {tabs.map((tb) => (
                <TabsContent key={tb.id} value={tb.id}>
                  {tb.panel}
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>
      </div>
    </div>
  );
}
