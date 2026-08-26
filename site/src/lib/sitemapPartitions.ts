/*
 * Sitemap partition builder (spec §10.1) — one partition per section per
 * locale. Partition == generated static routes × ledger availability; the URL
 * set is EXACTLY what the build generates crossed with ledger membership.
 * lastmod = the extraction build's stamp, NEVER wall-clock (AC S14): the run
 * date recorded in extracted/EXTRACTION-LOG.md for buildId 19029065
 * (2026-08-24), pinned via MISIDE_BUILD_DATE on reruns.
 */
import { LOCALES } from "@/i18n/locales";
import { kindAvailable } from "@/data/availability";
import { kindIds } from "@/data/contracts";
import { INDEX_SEGMENTS, KIND_SEGMENT } from "@/lib/routes";

export const BUILD_STAMP =
  process.env.MISIDE_BUILD_DATE ?? "2026-08-24";

const KIND_SECTIONS = [
  "mita",
  "players",
  "cartridges",
  "minigames",
  "achievements",
  "endings",
  "books",
  "locations",
] as const;

/** Partition ids: "<section>@<locale>", ledger-admitted only. */
export function sitemapPartitionIds(): string[] {
  const ids: string[] = [];
  const sections = ["home", ...INDEX_SEGMENTS, ...KIND_SECTIONS];
  for (const section of sections) {
    const gate =
      section === "home" || section === "map"
        ? "mita"
        : INDEX_SEGMENTS.includes(section as never)
          ? section === "lore/books"
            ? "books"
            : section === "guides" ||
                section === "news" ||
                section === "tools" ||
                section === "glossary" ||
                section === "media" ||
                section === "devlog" ||
                section === "feedback"
              ? "achievements"
              : section
          : section;
    for (const locale of LOCALES) {
      if (!kindAvailable(locale.code, gate)) continue;
      ids.push(`${section}@${locale.code}`);
    }
  }
  return ids;
}

/** URLs of one partition, canonical forms only (home has no trailing slash). */
export function partitionUrls(id: string): string[] {
  const at = id.lastIndexOf("@");
  if (at < 1) return [];
  const section = id.slice(0, at);
  const def = LOCALES.find((l) => l.code === id.slice(at + 1));
  if (!def) return [];
  const prefix = def.prefix;

  if (section === "home") return [prefix || "/"];
  if ((KIND_SECTIONS as readonly string[]).includes(section)) {
    const segment = KIND_SEGMENT[section];
    return [`${prefix}/${segment}`, ...kindIds(section).map((i) => `${prefix}/${segment}/${i}`)];
  }
  if (INDEX_SEGMENTS.includes(section as never)) return [`${prefix}/${section}`];
  return [];
}
