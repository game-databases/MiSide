import { revalidatePath } from "next/cache";
import { NextResponse } from "next/server";

/*
 * On-demand revalidation (spec §1.2): called by the pipeline emit stage after
 * a rerun, shared secret. A stale record after a patch rerun is a defect —
 * this is the ISR-grade reason Next was chosen.
 */
export async function POST(request: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "not configured" }, { status: 503 });
  }
  const provided =
    request.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ??
    new URL(request.url).searchParams.get("secret");
  if (provided !== secret) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  let path = new URL(request.url).searchParams.get("path") ?? "/";
  // revalidatePath wants the canonical path without locale games
  if (path.startsWith("/en/") || path === "/en") {
    path = path.slice(3) || "/";
  }
  revalidatePath(path);
  return NextResponse.json({ revalidated: true, path });
}
