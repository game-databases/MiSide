import "../globals.css";

import { SiteChrome } from "@/components/routes/SiteChrome";
import { HtmlShell, htmlMetadata } from "@/components/routes/HtmlShell";
import { getChrome } from "@/i18n/request";
import { getLocale } from "@/i18n/locales";
import { availableLocalesFor } from "@/data/availability";
import { buildId } from "@/data/contracts";

/*
 * Pivot chrome layout — EN serves at BARE paths (DR-2026-08-20-locale-urls).
 * This group is one of the site's TWO ROOT layouts: it owns <html> and
 * declares the pivot's lang/dir. The [locale] tree mirrors every route below
 * with its own validated root layout.
 */
export const metadata = htmlMetadata;

export default function PivotLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const def = getLocale("en")!;
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
