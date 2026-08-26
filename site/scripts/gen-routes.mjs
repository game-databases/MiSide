/*
 * Generates the (pivot) + [locale] twin route trees from one template set —
 * every file <15 lines delegating to src/components/routes implementations
 * (spec §2 rules: no route logic exists twice). Deterministic; rerun-safe.
 * Run: node scripts/gen-routes.mjs
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const appDir = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "src",
  "app"
);

const PIVOT = join(appDir, "(pivot)");
const LOCTREE = join(appDir, "[locale]");

// kind → [route segment, id param]
const KINDS = {
  mita: ["mita", "character_id"],
  players: ["players", "character_id"],
  cartridges: ["cartridges", "cartridge_id"],
  minigames: ["minigames", "minigame_id"],
  achievements: ["achievements", "achievement_id"],
  endings: ["endings", "ending_id"],
};
const BOOKS = ["lore/books", "book_id"];
const LORE = ["lore", "document_id"];
const PROFILES = ["lore/profiles", "document_id"];
const LOCATIONS = ["locations", "scene_id"];
const DIALOGUE = ["dialogue/[container]", "container"];
const SEG_FOR = {
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
const STUBS = [
  "tools",
  "glossary",
  "media",
  "devlog",
  "feedback",
];
// content pipeline (M3/M4) — real section factories, not stubs
const CONTENT_SECTIONS = [
  { seg: "guides", param: "guide_slug" },
  { seg: "news", param: "news_slug" },
];

function contentRoutes() {
  /* ---------- pivot index + detail ---------- */
  for (const { seg, param } of CONTENT_SECTIONS) {
    write(
      join(PIVOT, seg, "page.tsx"),
      `
import {
  ArticleIndexContent,
  buildArticleIndexMetadata,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export default function Page() {
  return ArticleIndexContent({ section: "${seg}", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildArticleIndexMetadata("${seg}", "en");
}
`
    );
    write(
      join(PIVOT, seg, `[${param}]`, "page.tsx"),
      `
import {
  ArticleContent,
  buildArticleMetadata,
  articleParamsPivot,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export const dynamicParams = false;

export default async function Page({
  params,
}: {
  params: Promise<{ ${param}: string }>;
}) {
  const { ${param} } = await params;
  return ArticleContent({ section: "${seg}", slug: ${param}, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<{ ${param}: string }>;
}): Promise<Metadata> {
  const { ${param} } = await args.params;
  return buildArticleMetadata("${seg}", ${param}, "en");
}
export function generateStaticParams() {
  return articleParamsPivot("${seg}");
}
`
    );
  }
  /* ---------- [locale] mirrors ---------- */
  for (const { seg, param } of CONTENT_SECTIONS) {
    write(
      join(LOCTREE, seg, "page.tsx"),
      `
import {
  ArticleIndexContent,
  buildArticleIndexMetadata,
} from "@/components/routes/articlePages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return ArticleIndexContent({ section: "${seg}", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildArticleIndexMetadata("${seg}", locale);
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
`
    );
    write(
      join(LOCTREE, seg, `[${param}]`, "page.tsx"),
      `
import {
  ArticleContent,
  buildArticleMetadata,
  articleParamsByLocale,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export const dynamicParams = false;

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; ${param}: string }>;
}) {
  const { locale, ${param} } = await params;
  return ArticleContent({ section: "${seg}", slug: ${param}, localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string; ${param}: string }>;
}): Promise<Metadata> {
  const { locale, ${param} } = await args.params;
  return buildArticleMetadata("${seg}", ${param}, locale);
}
export function generateStaticParams() {
  return articleParamsByLocale("${seg}");
}
`
    );
  }
}
contentRoutes();

function write(file, body) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, body.trimStart() + "\n", "utf8");
}

/* ---------- pivot index pages ---------- */
for (const [kind] of Object.entries(KINDS)) {
  const seg = KINDS[kind][0];
  write(
    join(PIVOT, seg, "page.tsx"),
    `
import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return <EntityIndexContent kind="${kind}" localeCode="en" />;
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "${SEG_FOR[kind]}", "nav.${kind}");
}
`
  );
}
for (const [seg, kind] of [
  [BOOKS[0], "books"],
  [LOCATIONS[0], "locations"],
]) {
  write(
    join(PIVOT, seg, "page.tsx"),
    `
import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return <EntityIndexContent kind="${kind}" localeCode="en" />;
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "${SEG_FOR[kind]}", "nav.${kind}");
}
`
  );
}

/* ---------- pivot detail pages ---------- */
for (const [kind, [seg, param]] of Object.entries(KINDS)) {
  write(
    join(PIVOT, seg, `[${param}]`, "page.tsx"),
    `
import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParams,
} from "@/components/routes/entityPages";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<Record<string, string>>;
}) {
  return EntityDetailContent({ kind: "${kind}", param: "${param}", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "${kind}", param: "${param}", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("${kind}", "${param}");
}
`
  );
}
for (const [dir, param, kind] of [
  [PROFILES[0], PROFILES[1], "profiles"],
  [LORE[0], LORE[1], "lore"],
  [BOOKS[0], BOOKS[1], "books"],
  [LOCATIONS[0], LOCATIONS[1], "locations"],
]) {
  write(
    join(PIVOT, dir, `[${param}]`, "page.tsx"),
    `
import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParams,
} from "@/components/routes/entityPages";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<Record<string, string>>;
}): Promise<ReturnType<typeof EntityDetailContent>> {
  return EntityDetailContent({ kind: "${kind}", param: "${param}", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "${kind}", param: "${param}", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("${kind}", "${param}");
}
`
  );
}
write(
  join(PIVOT, "dialogue", "[container]", "page.tsx"),
  `
import { DialogueGraphRoute } from "@/components/routes/DialogueGraphRoute";
import { getChrome } from "@/i18n/request";
import { dialogueContainers } from "@/components/routes/DialogueGraphRoute";

export default async function Page({
  params,
}: {
  params: Promise<{ container: string }>;
}) {
  const { container } = await params;
  const chrome = getChrome("en") as unknown as Record<string, string>;
  return (
    <DialogueGraphRoute
      container={container}
      localePrefix=""
      homeLabel={chrome["breadcrumb.home"]}
      chrome={chrome}
    />
  );
}
export function generateStaticParams() {
  return dialogueContainers().map((container) => ({ container }));
}
`
);

/* ---------- pivot stub sections ---------- */
for (const seg of STUBS) {
  write(
    join(PIVOT, seg, "page.tsx"),
    `
import {
  StubSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return StubSectionContent({ segment: "${seg}", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "${seg}", "nav.${seg}");
}
`
  );
}
write(
  join(PIVOT, "map", "page.tsx"),
  `
import {
  MapSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return MapSectionContent({ localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "map", "nav.map");
}
`
);
write(
  join(PIVOT, "account", "[[...slot]]", "page.tsx"),
  `
import { AccountSlotContent } from "@/components/routes/sectionPages";

export default function Page() {
  // Reserved tracker/account slot — auth provider is a per-pack build-time call.
  return AccountSlotContent({ localeCode: "en" });
}
`
);

/* ---------- home pages ---------- */
write(
  join(PIVOT, "page.tsx"),
  `
import {
  HomePageContent,
  buildHomeMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return HomePageContent({ localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildHomeMetadata("en");
}
`
);
write(
  join(LOCTREE, "page.tsx"),
  `
import {
  HomePageContent,
  buildHomeMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return HomePageContent({ localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildHomeMetadata(locale);
}
`
);

/* ---------- [locale] tree mirrors ---------- */
write(
  join(LOCTREE, "layout.tsx"),
  `
import { notFound } from "next/navigation";
import { SiteChrome } from "@/components/routes/SiteChrome";
import { getChrome } from "@/i18n/request";
import { PREFIXED_LOCALES, getLocale } from "@/i18n/locales";
import { availableLocalesFor } from "@/data/availability";
import { buildId } from "@/data/contracts";

export const dynamicParams = false;

export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const def = getLocale(locale);
  if (!def || def.prefix === "") notFound(); // /{en}/* does not exist
  const chrome = getChrome(def) as unknown as Record<string, string>;
  return (
    <div dir={def.dir}>
      <SiteChrome
        locale={def}
        chrome={chrome}
        currentPath="/"
        availableLocales={availableLocalesFor("mita")}
        buildId={buildId()}
      >
        {children}
      </SiteChrome>
    </div>
  );
}
`
);

for (const [kind, [seg, param]] of Object.entries(KINDS)) {
  write(
    join(LOCTREE, seg, "page.tsx"),
    `
import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return EntityIndexContent({ kind: "${kind}", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildSectionMetadata(locale, "${SEG_FOR[kind]}", "nav.${kind}");
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
`
  );
  write(
    join(LOCTREE, seg, `[${param}]`, "page.tsx"),
    `
import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParamsByLocale,
} from "@/components/routes/entityPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string } & Record<string, string>>;
}) {
  const { locale, ...rest } = await params;
  return EntityDetailContent({ kind: "${kind}", param: "${param}", params: Promise.resolve(rest), localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string } & Record<string, string>>;
}): Promise<Metadata> {
  const { locale, ...rest } = await args.params;
  return EntityDetailMetadata({ kind: "${kind}", param: "${param}", params: Promise.resolve(rest), localeCode: locale });
}
export function generateStaticParams() {
  return entityIdParamsByLocale("${kind}", "${param}", PREFIXED_LOCALES.map((l) => l.code));
}
`
  );
}
for (const [dir, param, kind] of [
  [PROFILES[0], PROFILES[1], "profiles"],
  [LORE[0], LORE[1], "lore"],
  [BOOKS[0], BOOKS[1], "books"],
  [LOCATIONS[0], LOCATIONS[1], "locations"],
]) {
  write(
    join(LOCTREE, dir, "page.tsx"),
    `
import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return EntityIndexContent({ kind: "${kind}", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildSectionMetadata(locale, "${SEG_FOR[kind]}", "nav.${kind}");
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
`
  );
  write(
    join(LOCTREE, dir, `[${param}]`, "page.tsx"),
    `
import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParamsByLocale,
} from "@/components/routes/entityPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string } & Record<string, string>>;
}) {
  const { locale, ...rest } = await params;
  return EntityDetailContent({ kind: "${kind}", param: "${param}", params: Promise.resolve(rest), localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string } & Record<string, string>>;
}): Promise<Metadata> {
  const { locale, ...rest } = await args.params;
  return EntityDetailMetadata({ kind: "${kind}", param: "${param}", params: Promise.resolve(rest), localeCode: locale });
}
export function generateStaticParams() {
  return entityIdParamsByLocale("${kind}", "${param}", PREFIXED_LOCALES.map((l) => l.code));
}
`
  );
}
write(
  join(LOCTREE, "dialogue", "[container]", "page.tsx"),
  `
import { DialogueGraphRoute } from "@/components/routes/DialogueGraphRoute";
import { getChrome } from "@/i18n/request";
import { dialogueContainers } from "@/components/routes/DialogueGraphRoute";
import { getLocale } from "@/i18n/locales";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import { notFound } from "next/navigation";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; container: string }>;
}) {
  const { locale, container } = await params;
  const def = getLocale(locale);
  if (!def) notFound();
  const chrome = getChrome(def) as unknown as Record<string, string>;
  return (
    <DialogueGraphRoute
      container={container}
      localePrefix={def.prefix}
      homeLabel={chrome["breadcrumb.home"]}
      chrome={chrome}
    />
  );
}
export function generateStaticParams() {
  const out: Array<{ locale: string; container: string }> = [];
  for (const l of PREFIXED_LOCALES)
    for (const container of dialogueContainers()) out.push({ locale: l.code, container });
  return out;
}
`
);
for (const seg of STUBS) {
  write(
    join(LOCTREE, seg, "page.tsx"),
    `
import {
  StubSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return StubSectionContent({ segment: "${seg}", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildSectionMetadata(locale, "${seg}", "nav.${seg}");
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
`
  );
}
write(
  join(LOCTREE, "map", "page.tsx"),
  `
import {
  MapSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return MapSectionContent({ localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildSectionMetadata(locale, "map", "nav.map");
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
`
);
write(
  join(LOCTREE, "account", "[[...slot]]", "page.tsx"),
  `
import { AccountSlotContent } from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; slot?: string[] }>;
}) {
  const { locale } = await params;
  return AccountSlotContent({ localeCode: locale });
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code, slot: [] }));
}
`
);

console.log("route trees written under", appDir);
