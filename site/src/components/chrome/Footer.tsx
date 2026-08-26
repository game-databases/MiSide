import Link from "next/link";

import { INDEX_SEGMENTS, navLabelKey } from "@/lib/routes";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { asRoute } from "@/lib/utils";

/*
 * Chrome footer: full section link row + the visible buildId stamp
 * (user-facing provenance class only — no source identity, URLs or license
 * tags on pages, AGENTS.md rule 3 / DR-2026-08-15 D2). Machine-voice register
 * for the stamp (T2 §4.4).
 */
export function Footer({
  chrome,
  localePrefix,
  buildId,
}: {
  chrome: Record<string, string>;
  localePrefix: string;
  buildId: string;
}) {
  return (
    <footer className="mt-16 border-t border-border bg-[color-mix(in_srgb,var(--ms-bg-0)_88%,transparent)]">
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:grid-cols-2 lg:grid-cols-4">
        <nav aria-label={chrome["a11y.mainNav"]} className="flex flex-col items-start gap-1.5">
          {INDEX_SEGMENTS.slice(0, 8).map((seg) => (
            <Link
              key={seg}
              href={asRoute(`${localePrefix}/${seg}`)}
              className="rounded-full px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              {chrome[navLabelKey(seg)]}
            </Link>
          ))}
        </nav>
        <nav aria-label={chrome["a11y.mainNav"]} className="flex flex-col items-start gap-1.5">
          {INDEX_SEGMENTS.slice(8).map((seg) => (
            <Link
              key={seg}
              href={asRoute(`${localePrefix}/${seg}`)}
              className="rounded-full px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              {chrome[navLabelKey(seg)]}
            </Link>
          ))}
        </nav>
        <div />
        <div className="flex flex-col items-start justify-end gap-2 sm:items-end">
          {/* visible data-version evidence — machine voice. The LABEL speaks
              chrome (any script) in Nunito; only the latin/digit id rides the
              LCD face — no mid-chip fallback mixing (VC-1 fix #7). */}
          <LcdTerminal className="w-auto text-sm">
            <span className="font-sans font-bold">{chrome["footer.buildLabel"]}</span>{" "}
            <span>{buildId}</span>
          </LcdTerminal>
        </div>
      </div>
    </footer>
  );
}
