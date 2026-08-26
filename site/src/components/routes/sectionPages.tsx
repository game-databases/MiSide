import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { CartridgeCard } from "@/components/kit/CartridgeCard";
import { GradientPill } from "@/components/kit/GradientPill";
import { getChrome } from "@/i18n/request";
import { getLocale, LOCALES } from "@/i18n/locales";
import { buildId, kindIds, readJsonl, scenes, ENTITY_KINDS } from "@/data/contracts";
import { resolveLoc } from "@/data/resolveLoc";
import { buildAlternates } from "@/lib/hreflang";
import { HomeRoute } from "./HomeRoute";
import { StubRoute } from "./EntityIndexRoute";
import { buildIndexData, desluggedLabel } from "./entityView";
import { MapRoute } from "./MapRoute";
import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";

/*
 * Section/home/map content factories shared by BOTH trees. Stubs render
 * chrome only where the spec says so (§8 non-goals); empty sections are
 * omitted by design, never captioned (anti-slop).
 */

const SECTION_TITLE_KEY: Record<string, string> = {
  guides: "nav.guides",
  news: "nav.news",
  tools: "nav.tools",
  glossary: "nav.glossary",
  media: "nav.media",
  devlog: "nav.devlog",
  feedback: "nav.feedback",
};

function chromeFor(localeCode: string) {
  const def = getLocale(localeCode);
  if (!def) notFound();
  return {
    def,
    chrome: getChrome(def) as unknown as Record<string, string>,
  };
}

/*
 * Unique localized title/description per locale (localization-architecture
 * §3): composed from the AUTHORED CHROME strings of that locale — never an
 * English passthrough. Home canonical is the bare "/" (DR-2026-08-18-page-size).
 */
export function buildHomeMetadata(localeCode: string): Metadata {
  const { def, chrome } = chromeFor(localeCode);
  return {
    // absolute: chrome titles already carry the product name — no template suffix
    title: { absolute: chrome["meta.title"] },
    description: chrome["meta.description"],
    alternates: {
      // no trailing slash on prefixed homes — /ru/ is the 308 form, /ru serves
      canonical: def.prefix || "/",
      languages: buildAlternates("/", LOCALES.map((l) => l.code)),
    },
  };
}

export function buildSectionMetadata(
  localeCode: string,
  segment: string,
  titleKey: string
): Metadata {
  const { def, chrome } = chromeFor(localeCode);
  const path = `${def.prefix}/${segment}`;
  return {
    title: chrome[titleKey] ?? segment,
    alternates: {
      canonical: path,
      languages: buildAlternates(`/${segment}`, LOCALES.map((l) => l.code)),
    },
  };
}

export function HomePageContent({ localeCode }: { localeCode: string }) {
  const { def, chrome } = chromeFor(localeCode);
  // per-cell counts grid — real row counts from the contract id columns
  const counts: Record<string, number> = {};
  for (const [kind, seg] of [
    ["mita", "mita"],
    ["players", "players"],
    ["cartridges", "cartridges"],
    ["minigames", "minigames"],
    ["achievements", "achievements"],
    ["endings", "endings"],
    ["books", "lore/books"],
    ["locations", "locations"],
  ] as const) {
    if (ENTITY_KINDS[kind]) counts[seg] = kindIds(kind).length;
  }
  // art-first lead module: Mitas that own a client portrait
  const featuredMitas = buildIndexData("mita", def.code, chrome["nav.mita"]).cards
    .filter((c) => Boolean(c.img))
    .map((c) => ({ id: c.id, href: c.href, name: c.title, img: c.img, accent: c.accent }));
  // featured-content row (VC-2 fix #7): every dialogue carrier with its
  // node count; titles ride the scene chapter names where the client names
  // them (per locale), honestly re-spaced ids otherwise.
  const featuredDialogue = featuredDialogueRows(def.code, def.prefix);
  return (
    <HomeRoute
      locale={def}
      chrome={chrome}
      buildId={buildId()}
      counts={counts}
      featuredMitas={featuredMitas}
      featuredDialogue={featuredDialogue}
    />
  );
}

/** Dialogue carriers → {href,title,nodes}; shipped datasets only. */
function featuredDialogueRows(localeCode: string, prefix: string) {
  const nodes = readJsonl<{ id: string }>("data/dialogue/nodes.jsonl", "id").rows;
  const perLevel = new Map<string, number>();
  for (const n of nodes) {
    const lvl = n.id.split(":")[0];
    perLevel.set(lvl, (perLevel.get(lvl) ?? 0) + 1);
  }
  const chapterLoc = new Map<string, { category: string; line_index: number }>();
  for (const s of scenes()) {
    if (s.chapter_name_loc) chapterLoc.set(s.scene_id, s.chapter_name_loc);
  }
  return [...perLevel.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([lvl, nodeCount]) => {
      const ptr = chapterLoc.get(lvl);
      const named = ptr ? resolveLoc(localeCode, ptr) : "";
      return {
        href: `${prefix}/dialogue/${lvl}`,
        title: named || desluggedLabel(lvl) || lvl,
        nodes: nodeCount,
      };
    });
}

/*
 * /dialogue index (VC-3 fix #4) — the section's own named page instead of
 * the sitewide default title: the same metadata law as every other index
 * (unique localized title, canonical + hreflang cluster), and the same
 * carrier cards the home transcript rail uses, with their node counts.
 */
export function buildDialogueIndexMetadata(localeCode: string): Metadata {
  const { def, chrome } = chromeFor(localeCode);
  return {
    title: chrome["nav.dialogue"],
    alternates: {
      canonical: `${def.prefix}/dialogue`,
      languages: buildAlternates("/dialogue", LOCALES.map((l) => l.code)),
    },
  };
}

export function DialogueIndexContent({ localeCode }: { localeCode: string }) {
  const { def, chrome } = chromeFor(localeCode);
  const carriers = featuredDialogueRows(def.code, def.prefix);
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={def.prefix}
        segments={["dialogue"]}
        labels={{ dialogue: chrome["nav.dialogue"] }}
        homeLabel={chrome["breadcrumb.home"]}
      />
      <GradientPill className="w-fit">{chrome["nav.dialogue"]}</GradientPill>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {carriers.map((d) => (
          <CartridgeCard
            key={d.href}
            href={d.href}
            title={d.title}
            count={`nodes:${d.nodes}`}
          />
        ))}
      </div>
    </div>
  );
}

export function StubSectionContent({
  segment,
  localeCode,
}: {
  segment: string;
  localeCode: string;
}) {
  const { def, chrome } = chromeFor(localeCode);
  return (
    <StubRoute
      title={chrome[SECTION_TITLE_KEY[segment]] ?? segment}
      localePrefix={def.prefix}
      segment={segment}
      homeLabel={chrome["breadcrumb.home"]}
    />
  );
}

export function MapSectionContent({ localeCode }: { localeCode: string }) {
  const { def, chrome } = chromeFor(localeCode);
  return (
    <div className="flex flex-col gap-6">
      <Breadcrumbs
        localePrefix={def.prefix}
        segments={["map"]}
        labels={{ map: chrome["nav.map"] }}
        homeLabel={chrome["breadcrumb.home"]}
      />
      <h1 className="text-3xl font-bold uppercase tracking-wide">
        {chrome["nav.map"]}
      </h1>
      <MapRoute chrome={chrome} localePrefix={def.prefix} />
    </div>
  );
}

export function AccountSlotContent({ localeCode }: { localeCode: string }) {
  const { def, chrome } = chromeFor(localeCode);
  return (
    <StubRoute
      title="Account"
      localePrefix={def.prefix}
      segment="account"
      homeLabel={chrome["breadcrumb.home"]}
    />
  );
}

export const ALL_LOCALE_CODES = LOCALES.map((l) => l.code);
export const BUILD_ID_STAMP = buildId();
