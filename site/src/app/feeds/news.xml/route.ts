import { SITE_ORIGIN } from "@/lib/siteConfig";
import { buildRssChannel, type RssItem } from "@/lib/rss";
import { publishedArticles } from "@/data/articles";

/*
 * /feeds/news.xml — game + database streams (content-pipeline spec §3.2/§7).
 * Items come from the M2 REGISTRY read server-side (no fetch, no client
 * bundle); the pivot EN cell carries the feed text. A zero-item stream is a
 * valid empty <channel> (§7.4). Patch diffs ride /feeds/patch.xml.
 */
export const contentType = "application/xml";
export const dynamic = "force-static";

const NEWS_STREAM_TYPES = new Set(["game", "database"]);

export function GET() {
  const items: RssItem[] = publishedArticles()
    .filter((r) => NEWS_STREAM_TYPES.has(r.type) && r.locales.en)
    .map((r) => ({
      title: r.locales.en.title,
      link: `${SITE_ORIGIN}${r.locales.en.path}`,
      guid: `${SITE_ORIGIN}${r.locales.en.path}`,
      pubDate: r.published_at,
      description: r.locales.en.description,
    }));
  return new Response(
    buildRssChannel({
      title: "MiSide Database — News",
      link: `${SITE_ORIGIN}/news`,
      description: "News and data updates for MiSide.",
      items,
    }),
    { headers: { "content-type": "application/xml; charset=utf-8" } }
  );
}
