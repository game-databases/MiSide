import type { MetadataRoute } from "next";

import { SITE_ORIGIN } from "@/lib/siteConfig";

/*
 * robots discipline (seo-standard §2): AI crawler access is deliberate policy
 * — search/answer fetchers AND training crawlers are allowed; no internal
 * search results to noindex because /search has NO route by ruling. The word
 * "search" appears nowhere in this file or any sitemap. The Sitemap line is
 * an ABSOLUTE URL (protocol requirement).
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/api/revalidate"] }],
    sitemap: `${SITE_ORIGIN}/sitemap.xml`,
  };
}
