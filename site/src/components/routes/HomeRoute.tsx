import Link from "next/link";

import { CartridgeCard } from "@/components/kit/CartridgeCard";
import { GradientPill } from "@/components/kit/GradientPill";
import { HeartWallpaper } from "@/components/kit/HeartWallpaper";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { KIND_SECTION_ART, UI_ART } from "@/data/art";
import { INDEX_SEGMENTS, navLabelKey } from "@/lib/routes";
import { asRoute } from "@/lib/utils";
import type { LocaleDef } from "@/i18n/locales";
import type { Chrome } from "@/i18n/request";

/*
 * Home (VC-1 de-narration): opens on the object, never an introduction —
 * no page-defining sentence, no pill labelling the page the user is on
 * (design-standard §5.4). One data module up front: the Mita portrait rail,
 * then the section grid in the game's cartridge-card language with per-cell
 * counts (T2 §7.4); below it ONE featured-content module (VC-2 fix #7):
 * the transcript rail — every named dialogue carrier with its node count.
 */
export function HomeRoute({
  locale,
  chrome,
  buildId,
  counts,
  featuredMitas,
  featuredDialogue,
}: {
  locale: LocaleDef;
  chrome: Chrome;
  buildId: string;
  /** Per-kind row counts for the per-cell counts grid. */
  counts: Record<string, number>;
  /** Mitas with client portraits — the art-first lead module. */
  featuredMitas: Array<{
    id: string;
    href: string;
    name: string;
    img?: string;
    accent?: string;
  }>;
  /** Named dialogue carriers with their shipped node counts. */
  featuredDialogue: Array<{
    href: string;
    title: string;
    nodes: number;
  }>;
}) {
  return (
    <div className="flex flex-col gap-10">
      <section className="flex flex-col items-start gap-5">
        <HeartWallpaper className="-mx-4 w-[calc(100%+2rem)] p-8">
          <h1 className="text-4xl font-bold">
            <span className="ms-glow-pulse inline-block rounded-full bg-primary px-4 py-1 text-primary-foreground shadow-glow-pink">
              MiSide
            </span>
          </h1>
        </HeartWallpaper>
        {/* visible data-version evidence */}
        <LcdTerminal className="w-fit font-lcd text-sm">
          <span className="font-sans font-bold">{chrome["footer.buildLabel"]}</span>{" "}
          <span className="font-lcd">{buildId}</span>
        </LcdTerminal>
      </section>

      {featuredMitas.length > 0 && (
        <section aria-label={chrome["nav.mita"]}>
          <GradientPill className="mb-4">{chrome["nav.mita"]}</GradientPill>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {featuredMitas.map((m) => (
              <CartridgeCard
                key={m.id}
                href={m.href}
                title={m.name}
                img={m.img}
                imgAlt={m.name}
                accent={m.accent}
                className="w-36 shrink-0"
              />
            ))}
          </div>
        </section>
      )}

      <section aria-label={chrome["meta.title"]}>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {INDEX_SEGMENTS.filter((s) => s !== "map").map((seg) => (
            <CartridgeCard
              key={seg}
              href={asRoute(`${locale.prefix}/${seg}`)}
              title={chrome[navLabelKey(seg)]}
              count={counts[seg]}
              img={sectionArt(seg)}
            />
          ))}
        </div>
      </section>

      {featuredDialogue.length > 0 && (
        <section aria-label={chrome["nav.dialogue"]}>
          <GradientPill className="mb-4">{chrome["nav.dialogue"]}</GradientPill>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {featuredDialogue.map((d) => (
              <CartridgeCard
                key={d.href}
                href={d.href}
                title={d.title}
                count={`nodes:${d.nodes}`}
                className="w-44 shrink-0"
              />
            ))}
          </div>
        </section>
      )}

      <section className="flex flex-wrap gap-2">
        <Link
          href={asRoute(`${locale.prefix}/map`)}
          className="inline-flex h-10 items-center rounded-full bg-secondary px-5 text-sm font-bold uppercase tracking-wide hover:brightness-110"
        >
          {chrome["map.openMap"]}
        </Link>
      </section>
    </div>
  );
}

/**
 * Section-cell identity art only where the corpus holds a confident image —
 * the same table the section indexes use (VC-2 fix #3), so a section never
 * reads as bare checkerboard at home AND on its own index.
 */
function sectionArt(segment: string): string | undefined {
  if (segment === "mita") return "/img/mita/mita-usual.webp";
  if (segment === "lore/books") return UI_ART.book;
  return KIND_SECTION_ART[segment];
}
