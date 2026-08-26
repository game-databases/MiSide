/*
 * THE pinned 34-row locale table (spec.md §Locale strategy, three-way
 * reconcile 2026-08-24: 31↔31 store↔client exact + 3 client-only).
 * Single import site for every consumer — never hardcode a locale elsewhere.
 *
 * Columns: BCP-47 code · client dir name (join key into
 * extracted/localization/<dir>/ and into locale_availability.jsonl, which keys
 * locales by CLIENT dir name) · text direction · URL prefix · optional
 * chromeAlias.
 *
 * Exactly two declared aliases (spec scaffold §3.3): `ru-x-prerev → ru` and
 * `ar-EG → ar`. Any further alias is a defect.
 */

export type TextDirection = "ltr" | "rtl";

export interface LocaleDef {
  /** BCP-47 code; also the URL prefix segment (pivot has none). */
  code: string;
  /** Client directory name under extracted/localization/ — the ledger join key. */
  dirName: string;
  dir: TextDirection;
  /** Bare paths for the pivot; `/code` for everyone else. */
  prefix: string;
  /** Declared chrome-file alias. Only ru-x-prerev→ru and ar-EG→ar may exist. */
  chromeAlias?: "ru" | "ar";
}

export const PIVOT_LOCALE = "en";

export const LOCALES: readonly LocaleDef[] = [
  { code: "en", dirName: "English", dir: "ltr", prefix: "" },
  { code: "ru", dirName: "Russian", dir: "ltr", prefix: "/ru" },
  { code: "uk", dirName: "Ukrainian", dir: "ltr", prefix: "/uk" },
  { code: "be", dirName: "Belarusian", dir: "ltr", prefix: "/be" },
  { code: "bg", dirName: "Bulgarian", dir: "ltr", prefix: "/bg" },
  { code: "zh-Hans", dirName: "ChineseSimplified", dir: "ltr", prefix: "/zh-Hans" },
  { code: "zh-Hant", dirName: "ChineseTraditional", dir: "ltr", prefix: "/zh-Hant" },
  { code: "hr", dirName: "Croatian", dir: "ltr", prefix: "/hr" },
  { code: "cs", dirName: "Czech", dir: "ltr", prefix: "/cs" },
  { code: "fil", dirName: "Filipino", dir: "ltr", prefix: "/fil" },
  { code: "fr", dirName: "French", dir: "ltr", prefix: "/fr" },
  { code: "de", dirName: "German", dir: "ltr", prefix: "/de" },
  { code: "hu", dirName: "Hungarian", dir: "ltr", prefix: "/hu" },
  { code: "id", dirName: "Indonesia", dir: "ltr", prefix: "/id" },
  { code: "it", dirName: "Italian", dir: "ltr", prefix: "/it" },
  { code: "ja", dirName: "Japanese", dir: "ltr", prefix: "/ja" },
  { code: "kk", dirName: "Kazakh", dir: "ltr", prefix: "/kk" },
  { code: "ko", dirName: "Korean", dir: "ltr", prefix: "/ko" },
  // Spec §3.1 pins direction `rtl` ONLY for ar/ar-EG. NOTE (SB-1 finding,
  // logged): Persian is natively RTL; the spec letter keeps `fa` LTR until a
  // spec amendment lands — flagged, not silently changed.
  { code: "fa", dirName: "Persian", dir: "ltr", prefix: "/fa" },
  { code: "pl", dirName: "Polish", dir: "ltr", prefix: "/pl" },
  { code: "pt-PT", dirName: "Portugues Portugal", dir: "ltr", prefix: "/pt-PT" },
  { code: "pt-BR", dirName: "Português-Brasil", dir: "ltr", prefix: "/pt-BR" },
  { code: "ro", dirName: "Romanian", dir: "ltr", prefix: "/ro" },
  { code: "sr-Latn", dirName: "Serbian (Latin)", dir: "ltr", prefix: "/sr-Latn" },
  { code: "sk", dirName: "Slovak", dir: "ltr", prefix: "/sk" },
  { code: "es-419", dirName: "Spanish (LatinAmerica)", dir: "ltr", prefix: "/es-419" },
  { code: "es-ES", dirName: "Spanish (Spain)", dir: "ltr", prefix: "/es-ES" },
  { code: "sv", dirName: "Swedish", dir: "ltr", prefix: "/sv" },
  { code: "th", dirName: "Thai", dir: "ltr", prefix: "/th" },
  { code: "tr", dirName: "Turkish", dir: "ltr", prefix: "/tr" },
  { code: "vi", dirName: "Vietnamese", dir: "ltr", prefix: "/vi" },
  { code: "ar", dirName: "Arabic", dir: "rtl", prefix: "/ar" },
  { code: "ar-EG", dirName: "Arabic (Egyptian)", dir: "rtl", prefix: "/ar-EG", chromeAlias: "ar" },
  {
    code: "ru-x-prerev",
    dirName: "Pre-revolutionaryRussian",
    dir: "ltr",
    prefix: "/ru-x-prerev",
    chromeAlias: "ru",
  },
] as const;

export const LOCALE_CODES: readonly string[] = LOCALES.map((l) => l.code);
/** Prefixed locales only — the [locale] tree's generateStaticParams source. */
export const PREFIXED_LOCALES: readonly LocaleDef[] = LOCALES.filter(
  (l) => l.prefix !== "",
);

const BY_CODE = new Map(LOCALES.map((l) => [l.code, l]));
const BY_DIR_NAME = new Map(LOCALES.map((l) => [l.dirName, l]));

export function getLocale(code: string): LocaleDef | undefined {
  return BY_CODE.get(code);
}

/** Ledger join: client dir name → site locale. Unknown dirs fail callers loudly. */
export function localeByDirName(dirName: string): LocaleDef | undefined {
  return BY_DIR_NAME.get(dirName);
}

/** hreflang/prefix helper: bare path for the pivot, prefixed otherwise. */
export function localeHref(locale: string, path: string): string {
  const def = BY_CODE.get(locale);
  if (!def) throw new Error(`Unknown locale: ${locale}`);
  const suffix = path === "/" ? "" : path;
  return `${def.prefix}${suffix}` || "/";
}
