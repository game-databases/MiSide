/*
 * Map state is a URL (FRAMEWORK §2.6). Focus grammar pinned by the scenes
 * contract: `/map?focus=<entity_kind>:<entity_slug>&scene=<scene_id>`.
 */
export interface MapFocus {
  kind: string;
  slug: string;
  scene?: string;
}

export function formatFocus(focus: MapFocus): string {
  const params = new URLSearchParams();
  params.set("focus", `${focus.kind}:${focus.slug}`);
  if (focus.scene) params.set("scene", focus.scene);
  return `?${params.toString()}`;
}

export function parseFocus(
  search: URLSearchParams | Record<string, string | undefined>
): MapFocus | null {
  const get = (k: string): string | undefined =>
    search instanceof URLSearchParams
      ? (search.get(k) ?? undefined)
      : search[k];
  const raw = get("focus");
  if (!raw) return null;
  const sep = raw.indexOf(":");
  if (sep <= 0) return null;
  const kind = raw.slice(0, sep);
  const slug = raw.slice(sep + 1);
  if (!kind || !slug) return null;
  return { kind, slug, scene: get("scene") };
}
