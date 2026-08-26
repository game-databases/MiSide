import Link from "next/link";

import { cn } from "@/lib/utils";
import { HEADER_NAV_SEGMENTS, indexHref, navLabelKey } from "@/lib/routes";
import { SearchField } from "./SearchField";
import { asRoute } from "@/lib/utils";
import { LocaleCombobox } from "./LocaleCombobox";

/*
 * Chrome header: brand + nav words + the search field (closed = a word in the
 * nav; open it grows across this row) + locale combobox. Thin chrome over the
 * content below — never competes with the page object (design-standard §5.2).
 */
export function Header({
  chrome,
  localeCode,
  localePrefix,
  currentPath,
  availableLocales,
}: {
  chrome: Record<string, string>;
  localeCode: string;
  localePrefix: string;
  /** Current path without locale prefix (for locale switching same-page). */
  currentPath: string;
  availableLocales: readonly string[];
}) {
  return (
    <header className="relative z-40 border-b border-border bg-[color-mix(in_srgb,var(--ms-bg-0)_86%,transparent)] backdrop-blur">
      {/* wrap instead of collide (VC-1 fix #6): long RU/DE words reflow to a
          second row; the brand + controls keep their line */}
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3">
        <Link
          href={asRoute(localePrefix || "/")}
          className="rounded-full bg-primary px-4 py-1.5 font-bold uppercase tracking-wide text-primary-foreground shadow-glow-pink"
        >
          MiSide
        </Link>
        <nav aria-label={chrome["a11y.mainNav"]} className="hidden min-w-0 flex-1 flex-wrap items-center gap-1 lg:flex">
          {HEADER_NAV_SEGMENTS.map((seg) => (
            <Link
              key={seg}
              href={asRoute(indexHref(localePrefix, seg))}
              className="whitespace-nowrap rounded-full px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground xl:px-3"
            >
              {chrome[navLabelKey(seg)]}
            </Link>
          ))}
        </nav>
        <SearchField chrome={chrome} localeCode={localeCode} />
        <LocaleCombobox
          chrome={chrome}
          localeCode={localeCode}
          currentPath={currentPath}
          availableLocales={availableLocales}
        />
      </div>
      {/* small-screen row keeps every section reachable as plain anchors */}
      <nav
        aria-label={chrome["a11y.mainNav"]}
        className={cn("mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 pb-3 lg:hidden")}
      >
        {HEADER_NAV_SEGMENTS.map((seg) => (
          <Link
            key={seg}
            href={asRoute(indexHref(localePrefix, seg))}
            className="whitespace-nowrap rounded-full bg-secondary px-3 py-1.5 text-xs font-bold text-secondary-foreground"
          >
            {chrome[navLabelKey(seg)]}
          </Link>
        ))}
      </nav>
    </header>
  );
}
