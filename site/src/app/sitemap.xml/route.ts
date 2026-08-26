import { sitemapPartitionIds } from "@/lib/sitemapPartitions";
import { SITE_ORIGIN } from "@/lib/siteConfig";

/*
 * /sitemap.xml — the sitemap INDEX. Lists every section×locale partition
 * served at {origin}/sitemap/{section}@{locale}.xml. robots.txt points here;
 * zero orphan references. <loc> is protocol-required ABSOLUTE (sitemaps.org).
 */
export const contentType = "application/xml";
export const dynamic = "force-static";

export function GET() {
  const entries = sitemapPartitionIds()
    .map((id) => `  <sitemap><loc>${SITE_ORIGIN}/sitemap/${encodeURIComponent(id)}.xml</loc></sitemap>`)
    .join("\n");
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</sitemapindex>\n`,
    { headers: { "content-type": "application/xml; charset=utf-8" } }
  );
}
