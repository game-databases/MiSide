/*
 * RSS 2.0 channel builder for /feeds/*.xml (content-pipeline spec §3.2):
 * pure string composition so node --test can parse the output directly.
 * A zero-item stream is a VALID EMPTY <channel> — the honest skeleton shape
 * (§7.4), never placeholder cards or captions.
 */

export interface RssItem {
  title: string;
  /** Absolute URL (SITE_ORIGIN + serving path). */
  link: string;
  guid: string;
  /** ISO date (YYYY-MM-DD) — emitted RFC-822. */
  pubDate: string;
  description?: string;
}

export function xmlEscape(text: string): string {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function rfc822(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00Z`);
  return Number.isNaN(d.getTime()) ? isoDate : d.toUTCString();
}

export function buildRssChannel(opts: {
  title: string;
  link: string;
  description: string;
  items: RssItem[];
}): string {
  const itemXml = opts.items
    .map(
      (it) =>
        `    <item>\n` +
        `      <title>${xmlEscape(it.title)}</title>\n` +
        `      <link>${xmlEscape(it.link)}</link>\n` +
        `      <guid isPermaLink="true">${xmlEscape(it.guid)}</guid>\n` +
        `      <pubDate>${rfc822(it.pubDate)}</pubDate>\n` +
        (it.description
          ? `      <description>${xmlEscape(it.description)}</description>\n`
          : "") +
        `    </item>`
    )
    .join("\n");
  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<rss version="2.0">\n` +
    `  <channel>\n` +
    `    <title>${xmlEscape(opts.title)}</title>\n` +
    `    <link>${xmlEscape(opts.link)}</link>\n` +
    `    <description>${xmlEscape(opts.description)}</description>\n` +
    (itemXml ? `${itemXml}\n` : "") +
    `  </channel>\n` +
    `</rss>\n`
  );
}
