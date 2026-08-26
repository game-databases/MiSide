/*
 * hreflang cluster helper (AC S3): the cluster is EXACTLY the page's
 * locale_availability membership + self + x-default → bare path. Zero
 * entries may point at non-200 URLs — membership comes from the ledger, never
 * from assumptions.
 */
import { LOCALES } from "@/i18n/locales";
import type { SearchRow } from "@/lib/search/searchRows";

export interface HreflangEntry {
  hreflang: string; // BCP-47 code or "x-default"
  href: string;
}

/**
 * Build the alternates map for Next's metadata API: one entry per available
 * locale (prefixed except pivot-bare) plus x-default at the pivot path.
 * `availableLocales` = site codes admitted by the ledger for THIS page.
 */
export function buildAlternates(
  pathWithoutPrefix: string,
  availableLocales: readonly string[]
): Record<string, string> {
  const alternates: Record<string, string> = {};
  for (const code of availableLocales) {
    const def = LOCALES.find((l) => l.code === code);
    if (!def) continue;
    const suffix = pathWithoutPrefix === "/" ? "" : pathWithoutPrefix;
    alternates[code] = `${def.prefix}${suffix}` || "/";
  }
  // x-default → the pivot's bare path (localization-architecture §2)
  const enDef = LOCALES[0];
  const suffix = pathWithoutPrefix === "/" ? "" : pathWithoutPrefix;
  alternates["x-default"] = `${enDef.prefix}${suffix}` || "/";
  return alternates;
}

/** Cross-locale link row entries (the visible row inside EntityShell). */
export function crossLocaleRow(
  locale: string,
  kind: string,
  id: string,
  availableLocales: readonly string[]
): Array<{ code: string; label: string; href: string }> {
  return availableLocales
    .filter((c) => c !== locale)
    .map((code) => {
      const def = LOCALES.find((l) => l.code === code)!;
      return {
        code,
        label: code,
        href: entityPathFor(def.prefix, kind, id),
      };
    });
}

function entityPathFor(prefix: string, kind: string, id: string): string {
  return `${prefix}/${kind}/${id}`;
}

export type { SearchRow };
