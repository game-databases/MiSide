import type { Metadata } from "next";

import { GtagSnippet } from "@/components/routes/GtagSnippet";
import { LOCALES } from "@/i18n/locales";
import { SITE_ORIGIN } from "@/lib/siteConfig";

/*
 * The <html> shell both route-group roots render (multi-root layout: the
 * pivot group declares lang="en"/dir="ltr"; the [locale] group declares the
 * serving locale's own lang + dir — VC-1 fix #8: crawlers and AT read
 * direction and language from the DOCUMENT ELEMENT, so a wrapper div is not
 * compliance). Carries the font/token CSS import, skip link, GA4 gtag, and
 * the ONE sitewide server-rendered JSON-LD graph (spec §10.2).
 *
 * No SearchAction: there is no search route by ruling, and markup never
 * asserts a value the extracted data does not hold. `sameAs` stays omitted
 * until §8 registry surfaces exist at build time — never invented.
 */
export const htmlMetadata: Metadata = {
  title: {
    default: "MiSide Database",
    template: "%s — MiSide Database",
  },
  robots: { index: true, follow: true },
};

const BUILD_ID = process.env.MISIDE_BUILD_ID ?? "19029065";

// inLanguage = every locale the site actually publishes (34-row table) —
// never a hand-picked subset. The developer Organization is its own graph
// node, referenced by VideoGame.author via @id.
const jsonld = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${SITE_ORIGIN}/#website`,
      url: SITE_ORIGIN,
      name: "MiSide Database",
      inLanguage: LOCALES.map((l) => l.code),
    },
    {
      "@type": "Organization",
      "@id": `${SITE_ORIGIN}/#organization`,
      name: "AIHASTO",
      url: SITE_ORIGIN,
    },
    {
      "@type": "VideoGame",
      name: "MiSide",
      author: { "@id": `${SITE_ORIGIN}/#organization` },
      datePublished: "2024-12-10",
      gamePlatform: "PC (Windows)",
    },
  ],
};

export function HtmlShell({
  lang,
  dir,
  children,
}: {
  lang: string;
  dir: "ltr" | "rtl";
  children: React.ReactNode;
}) {
  return (
    <html lang={lang} dir={dir} suppressHydrationWarning>
      <body>
        <a
          href="#page-content"
          className="sr-only focus:not-sr-only focus:absolute focus:start-2 focus:top-2 focus:z-50 focus:rounded-full focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Skip to content
        </a>
        {children}
        {/* machine plane carries buildId + graph; visible stamps are per-page */}
        <script
          type="application/ld+json"
          data-build-id={BUILD_ID}
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonld) }}
        />
        <GtagSnippet />
      </body>
    </html>
  );
}
