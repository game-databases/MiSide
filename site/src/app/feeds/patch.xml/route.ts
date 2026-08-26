/*
 * /feeds/patch.xml skeleton — per-patch data diffs feed (D5 move 3 shape);
 * entries arrive with the pipeline changelog summaries.
 */
export const contentType = "application/xml";

const XML = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>MiSide Database — Patch diffs</title>
    <link>/news</link>
    <description>Per-build data changes for MiSide.</description>
  </channel>
</rss>
`;

export function GET() {
  return new Response(XML, {
    headers: { "content-type": "application/xml; charset=utf-8" },
  });
}
