import { ImageResponse } from "next/og";
import { notFound } from "next/navigation";

import { ENTITY_KINDS, kindIds, findRow, buildId } from "@/data/contracts";
import { displayName } from "@/components/routes/entityView";
import { paletteFloatsToHex } from "@/lib/palette";
import type { PersonageRow } from "@/data/contracts";

export const contentType = "image/png";

/*
 * Per-entity OG card renderer (spec §5 machine-plane row): owned-art path —
 * art classes copy into public/cdn at build (separate piece), so v0 renders
 * the entity's OWN accent over the token gradient with the name + buildId.
 * Achievement icons render the named explicit-missing state while
 * icon.status == "pending-export" (no invented imagery).
 */
export function generateStaticParams() {
  const out: Array<{ kind: string; slug: string }> = [];
  for (const kind of Object.keys(ENTITY_KINDS)) {
    for (const slug of kindIds(kind)) out.push({ kind, slug });
  }
  return out;
}

const SIZE = { width: 1200, height: 630 };

function GET(_req: Request, ctx: { params: Promise<{ kind: string; slug: string }> }) {
  return GET_impl(_req, ctx);
}

async function GET_impl(
  _req: Request,
  ctx: { params: Promise<{ kind: string; slug: string }> }
) {
  const { kind, slug } = await ctx.params;
  if (!ENTITY_KINDS[kind]) notFound();
  const row = findRow(kind, slug);
  if (!row) notFound();
  const name = displayName(kind, row, "en");
  const accent =
    kind === "mita"
      ? paletteFloatsToHex((row as unknown as PersonageRow).palette_color1)
      : "#ff009c"; // --ms-accent primitive value (T2 §6)
  const pendingIcon =
    kind === "achievements" &&
    (row as { icon?: { status?: string } }).icon?.status === "pending-export";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          padding: 64,
          background: "linear-gradient(135deg, #140316 0%, #4a1d5a 60%, #5a1565 100%)",
        }}
      >
        <div
          style={{
            width: 96,
            height: 12,
            borderRadius: 999,
            background: accent,
            marginBottom: 24,
            display: "flex",
          }}
        />
        <div style={{ fontSize: 88, fontWeight: 700, color: "#fffcff", display: "flex" }}>
          {name}
        </div>
        <div style={{ fontSize: 36, color: "#d4bcbb", marginTop: 12, display: "flex" }}>
          {pendingIcon ? `icon ${"pending-export"}` : `${kind} · ${slug}`}
        </div>
        <div style={{ fontSize: 28, color: "#08cb05", marginTop: 32, fontFamily: "monospace", display: "flex" }}>
          build {buildId()}
        </div>
      </div>
    ),
    SIZE
  );
}

export { GET };
