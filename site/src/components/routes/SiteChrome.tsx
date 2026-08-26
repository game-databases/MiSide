import { Header } from "@/components/chrome/Header";
import { Footer } from "@/components/chrome/Footer";
import type { LocaleDef } from "@/i18n/locales";
import type { Chrome } from "@/i18n/request";

/*
 * Shared chrome frame for BOTH route trees ((pivot) and [locale]) — the
 * layout logic exists once; the tree files stay thin (<15 lines, spec §2).
 * #page-content is the stable wrapper the header search hides/restores
 * IN PLACE (hidden attr — never unmounted).
 */
export function SiteChrome({
  locale,
  chrome,
  currentPath,
  availableLocales,
  buildId,
  children,
}: {
  locale: LocaleDef;
  chrome: Chrome;
  /** Current path WITHOUT locale prefix, starting "/". */
  currentPath: string;
  availableLocales: readonly string[];
  buildId: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <Header
        chrome={chrome}
        localeCode={locale.code}
        localePrefix={locale.prefix}
        currentPath={currentPath}
        availableLocales={availableLocales}
      />
      <main id="page-content" className="mx-auto w-full max-w-6xl px-4 py-8">
        {children}
      </main>
      <Footer
        chrome={chrome}
        localePrefix={locale.prefix}
        buildId={buildId}
      />
    </>
  );
}

/** dir attribute value per locale (RTL: ar/ar-EG per spec §3.1). */
export function dirFor(locale: LocaleDef): string {
  return locale.dir;
}
