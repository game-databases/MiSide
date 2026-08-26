import Link from "next/link";

import { breadcrumbTrail } from "@/lib/routes";
import { asRoute } from "@/lib/utils";

/*
 * Visible breadcrumbs + BreadcrumbList JSON-LD (seo-standard §1; spec §10.2:
 * positions derive from the shared breadcrumb trail in lib/routes.ts, never
 * per-page hand-rolls). Server-rendered script tag — no client injection.
 */
export function Breadcrumbs({
  localePrefix,
  segments,
  labels,
  homeLabel,
}: {
  localePrefix: string;
  /** URL segments of the current path (no locale prefix). */
  segments: string[];
  labels: Record<string, string>;
  homeLabel: string;
}) {
  const trail = breadcrumbTrail(localePrefix, segments, labels, homeLabel);
  const jsonld = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: trail.map((crumb, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: crumb.name,
      item: crumb.item,
    })),
  };
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonld) }}
      />
      <nav aria-label="Breadcrumb" className="mb-4 flex flex-wrap items-center gap-1 text-sm">
        {trail.map((crumb, i) => (
          <span key={crumb.item} className="flex items-center gap-1">
            {i > 0 && <span className="text-muted-foreground">/</span>}
            {i === trail.length - 1 ? (
              <span aria-current="page" className="text-muted-foreground">
                {crumb.name}
              </span>
            ) : (
              <Link href={asRoute(crumb.item)} className="rounded-full px-1.5 py-0.5 hover:bg-accent">
                {crumb.name}
              </Link>
            )}
          </span>
        ))}
      </nav>
    </>
  );
}
