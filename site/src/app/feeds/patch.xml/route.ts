import { SITE_ORIGIN } from "@/lib/siteConfig";
import { buildRssChannel, type RssItem } from "@/lib/rss";
import { streamRows } from "@/data/articles";

/*
 * /feeds/patch.xml — the patch stream feed. Schema-ready and EMPTY-HONEST
 * until LANE-A lands changelog summaries (spec §7.1): a valid empty channel
 * is the shipped skeleton shape, never placeholder items.
 */
export const contentType = "application/xml";
export const dynamic = "force-static";

export function GET() {
  const items: RssItem[] = streamRows("patch")
    .filter((r) => Boolean(r.locales.en))
    .map((r) => ({
      title: r.locales.en.title,
      link: `${SITE_ORIGIN}${r.locales.en.path}`,
      guid: `${SITE_ORIGIN}${r.locales.en.path}`,
      pubDate: r.published_at,
      description: r.locales.en.description,
    }));
  return new Response(
    buildRssChannel({
      title: "MiSide Database — Patch diffs",
      link: `${SITE_ORIGIN}/news`,
      description: "Per-build data changes for MiSide.",
      items,
    }),
    { headers: { "content-type": "application/xml; charset=utf-8" } }
  );
}
