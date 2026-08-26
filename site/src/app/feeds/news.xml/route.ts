/*
 * /feeds/news.xml skeleton (site-sections #23; spec §5 feeds row).
 * Items land with the News piece; an empty <channel> is the honest skeleton.
 */
export const contentType = "application/xml";

const XML = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>MiSide Database — News</title>
    <link>/news</link>
    <description>News and data updates for MiSide.</description>
  </channel>
</rss>
`;

export function GET() {
  return new Response(XML, {
    headers: { "content-type": "application/xml; charset=utf-8" },
  });
}
