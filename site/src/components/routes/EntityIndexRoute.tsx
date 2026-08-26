import { notFound } from "next/navigation";

import { CartridgeCard } from "@/components/kit/CartridgeCard";
import { GradientPill } from "@/components/kit/GradientPill";
import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { KIND_SECTION_ART } from "@/data/art";
import { EntityIndexData } from "./entityView";

/*
 * Generic section index — one shared implementation for every routed kind in
 * BOTH trees; route files stay thin. Grid = cartridge-card language (T2 §7.4).
 * VC-2 fix #3: the header carries the section's identity art where the corpus
 * holds a confident object, and cards carry per-entity art via indexArtFor —
 * no index ships a bare image-less grid where imagery exists.
 */
export function EntityIndexRoute({
  data,
  localePrefix,
  homeLabel,
}: {
  data: EntityIndexData;
  localePrefix: string;
  homeLabel: string;
}) {
  if (!data) notFound();
  const sectionArt = KIND_SECTION_ART[data.kind];
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={[data.segment]}
        labels={{ [data.segment]: data.title }}
        homeLabel={homeLabel}
      />
      <div className="flex items-center gap-4">
        <GradientPill className="w-fit">{data.title}</GradientPill>
        {/* section identity art (corpus UI objects; aria-hidden chrome) */}
        {sectionArt && (
          // eslint-disable-next-line @next/next/no-img-element -- static public asset
          <img
            src={sectionArt}
            alt=""
            width={64}
            height={64}
            loading="lazy"
            aria-hidden
            className="size-16 shrink-0 object-contain"
          />
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {data.cards.map((c) => (
          <CartridgeCard
            key={`${data.kind}:${c.id}`}
            href={c.href}
            title={c.title}
            img={c.img}
            imgAlt={c.img ? c.title : undefined}
            count={c.count}
            accent={c.accent}
            corrupted={c.corrupted}
          />
        ))}
      </div>
    </div>
  );
}

/** Chrome-only stub shell for section routes whose pieces land later (spec §8). */
export function StubRoute({
  title,
  localePrefix,
  segment,
  homeLabel,
  children,
}: {
  title: string;
  localePrefix: string;
  segment: string;
  homeLabel: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={[segment]}
        labels={{ [segment]: title }}
        homeLabel={homeLabel}
      />
      <h1 className="text-3xl font-bold uppercase tracking-wide">{title}</h1>
      {/* honest empty state = omission, never an absence sentence */}
      {children}
    </div>
  );
}
