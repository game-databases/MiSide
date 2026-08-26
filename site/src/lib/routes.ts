/*
 * Shared route table — every (pivot) and [locale] route module delegates here;
 * no route logic exists twice (spec §2 rules). Slugs come ONLY from contract
 * id columns via src/data/kindIds (AC S6); unknown slugs 404 upstream.
 */
import type { LocaleDef } from "@/i18n/locales";

/** URL segment per routed entity kind. */
export const KIND_SEGMENT: Record<string, string> = {
  mita: "mita",
  players: "players",
  cartridges: "cartridges",
  minigames: "minigames",
  achievements: "achievements",
  endings: "endings",
  profiles: "lore/profiles",
  lore: "lore",
  books: "lore/books",
  locations: "locations",
};

export function entityHref(locale: LocaleDef | string, kind: string, id: string): string {
  const prefix = typeof locale === "string" ? locale : locale.prefix;
  return `${prefix}/${KIND_SEGMENT[kind]}/${id}`;
}

export function indexHref(locale: LocaleDef | string, segment: string): string {
  const prefix = typeof locale === "string" ? locale : locale.prefix;
  return `${prefix}/${segment}`;
}

/** Static index routes that exist at scaffold time (sitemap + nav sources). */
export const INDEX_SEGMENTS = [
  "mita",
  "players",
  "cartridges",
  "minigames",
  "achievements",
  "endings",
  "lore/books",
  "locations",
  "guides",
  "news",
  "tools",
  "glossary",
  "media",
  "devlog",
  "feedback",
  "map",
] as const;

/** Header primary nav (word "Search" closed-state included per DR ruling). */
export const HEADER_NAV_SEGMENTS = [
  "mita",
  "cartridges",
  "minigames",
  "achievements",
  "endings",
  "locations",
  "lore/books",
  "guides",
  "news",
  "tools",
] as const;

/** Chrome key for a nav/index segment. */
export function navLabelKey(segment: string): string {
  if (segment === "lore/books") return "nav.books";
  const first = segment.split("/")[0];
  return `nav.${first}`;
}

/**
 * Breadcrumb trail from URL segments — positions derive from THIS shared
 * trail (BreadcrumbList law, spec §10.2); never per-page hand-rolls.
 */
export function breadcrumbTrail(
  localePrefix: string,
  segments: string[],
  labels: Record<string, string>,
  homeLabel: string
): Array<{ name: string; item: string }> {
  const trail: Array<{ name: string; item: string }> = [
    { name: homeLabel, item: localePrefix || "/" },
  ];
  let acc = localePrefix;
  for (const seg of segments) {
    acc += `/${seg}`;
    trail.push({
      name: labels[seg] ?? decodeURIComponent(seg),
      item: acc,
    });
  }
  return trail;
}
