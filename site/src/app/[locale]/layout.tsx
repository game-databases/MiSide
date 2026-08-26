import "../globals.css";

import { notFound } from "next/navigation";
import { SiteChrome } from "@/components/routes/SiteChrome";
import { HtmlShell, htmlMetadata } from "@/components/routes/HtmlShell";
import { getChrome } from "@/i18n/request";
import { PREFIXED_LOCALES, getLocale } from "@/i18n/locales";
import { availableLocalesFor } from "@/data/availability";
import { buildId } from "@/data/contracts";

/*
 * [locale] root layout — one of the site's TWO ROOT layouts. It owns <html>
 * and declares the serving locale's own lang + dir on the DOCUMENT ELEMENT
 * (VC-1 fix #8): crawlers and AT read direction and language there, so a
 * wrapper div is not compliance.
 */
export const metadata = htmlMetadata;

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
    <HtmlShell lang={def.code} dir={def.dir}>
      <SiteChrome
        locale={def}
        chrome={chrome}
        currentPath="/"
        availableLocales={availableLocalesFor("mita")}
        buildId={buildId()}
      >
        {children}
      </SiteChrome>
    </HtmlShell>
  );
}
