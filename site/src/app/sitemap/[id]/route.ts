import { BUILD_STAMP, partitionUrls, sitemapPartitionIds } from "@/lib/sitemapPartitions";
import { SITE_ORIGIN } from "@/lib/siteConfig";

/*
 * One sitemap partition per section per locale: /sitemap/{section}@{locale}.xml.
 * Every <loc> is a generated static route admitted by the ledger, emitted
 * ABSOLUTE (sitemaps.org — relative <loc> values are rejected); every entry
 * carries lastmod = the extraction build stamp (AC S14). Unknown ids → 404.
 */
export const contentType = "application/xml";
export const dynamic = "force-static";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const raw = await ctx.params.then((p) => {
    try {
      return decodeURIComponent(p.id);
    } catch {
      return p.id;
    }
  });
  // strip a trailing ".xml" if routed bare
  const id = raw.replace(/\.xml$/, "");
  if (!sitemapPartitionIds().includes(id)) {
    return new Response("Not found", { status: 404 });
  }
  const urls = partitionUrls(id);
  const body = urls
    .map((u) => `  <url><loc>${SITE_ORIGIN}${u}</loc><lastmod>${BUILD_STAMP}</lastmod></url>`)
    .join("\n");
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`,
    { headers: { "content-type": "application/xml; charset=utf-8" } }
  );
}

export function generateStaticParams() {
  return sitemapPartitionIds().map((id) => ({ id: encodeURIComponent(id) }));
}
