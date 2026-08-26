/*
 * Map state is a URL (FRAMEWORK §2.6). Grammar pinned by the scenes contract
 * and map-viewer §5/§4.1:
 *
 *   /map?focus=<entity_kind>:<entity_slug>&scene=<scene_id>&kinds=<a,b,c>
 *
 * History law (A-MV1 OQ-5, pinned in map-viewer §5):
 *   • replaceState — filter toggles, focus changes, focus clear, ?kinds=
 *     edits (typing-law: a keystroke never fills the back button);
 *   • pushState   — scene change only, so Back walks the scene trail;
 *   • cold load restores whatever the URL carries.
 * `kinds` is ORDERED + DEDUPED (canonical vocabulary order); absent = every
 * kind enabled.
 */

export interface MapFocus {
  kind: string;
  slug: string;
  scene?: string;
}

type Search = string | URLSearchParams | Record<string, string | undefined>;

function asParams(search: Search): URLSearchParams {
  if (search instanceof URLSearchParams) return search;
  return new URLSearchParams(
    typeof search === "string" ? search : undefined
  );
}

function getParam(search: Search, k: string): string | undefined {
  if (typeof search === "string") return asParams(search).get(k) ?? undefined;
  return search instanceof URLSearchParams
    ? (search.get(k) ?? undefined)
    : search[k];
}

export function formatFocus(focus: MapFocus): string {
  const params = new URLSearchParams();
  params.set("focus", `${focus.kind}:${focus.slug}`);
  if (focus.scene) params.set("scene", focus.scene);
  return `?${params.toString()}`;
}

export function parseFocus(search: Search): MapFocus | null {
  const raw = getParam(search, "focus");
  if (!raw) return null;
  const sep = raw.indexOf(":");
  if (sep <= 0) return null;
  const kind = raw.slice(0, sep);
  const slug = raw.slice(sep + 1);
  if (!kind || !slug) return null;
  return { kind, slug, scene: getParam(search, "scene") };
}

/** The full viewer state the URL carries. */
export interface MapUrlState {
  focus: MapFocus | null;
  scene: string | null;
  /** Enabled kinds; null = no explicit selection (all enabled). */
  kinds: string[] | null;
}

export function parseMapState(search: Search): MapUrlState {
  const rawKinds = getParam(search, "kinds");
  let kinds: string[] | null = null;
  if (typeof rawKinds === "string") {
    // ordered + deduped; empty segments dropped
    const seen = new Set<string>();
    kinds = [];
    for (const part of rawKinds.split(",")) {
      const k = part.trim();
      if (k.length > 0 && !seen.has(k)) {
        seen.add(k);
        kinds.push(k);
      }
    }
  }
  return {
    focus: parseFocus(search),
    scene: getParam(search, "scene") ?? null,
    kinds,
  };
}

/**
 * Querystring for a state, preserving any foreign params via `base`.
 * `kinds`: undefined → param untouched by this edit; null → param removed
 * (Show All); array → ordered deduped value.
 */
export function buildMapSearch(
  base: Search,
  next: Partial<{
    focus: MapFocus | null;
    scene: string | null;
    kinds: string[] | null | undefined;
  }>
): string {
  const params = asParams(base);
  if (next.focus !== undefined) {
    params.delete("focus");
    if (next.focus) params.set("focus", `${next.focus.kind}:${next.focus.slug}`);
  }
  if (next.scene !== undefined) {
    if (next.scene) params.set("scene", next.scene);
    else params.delete("scene");
  }
  if (next.kinds !== undefined) {
    if (next.kinds === null) {
      // Show All — no explicit selection
      params.delete("kinds");
    } else {
      // [] stays EXPLICIT (?kinds= = nothing enabled); ordered + deduped
      const value = [...new Set(next.kinds)].join(",");
      if (value.length > 0) params.set("kinds", value);
      else params.set("kinds", "");
    }
  }
  const q = params.toString();
  return q ? `?${q}` : "";
}

/**
 * The two history verbs of the OQ-5 law. No-op off-browser (SSG render).
 * Returns nothing; callers keep React state as the source of truth.
 */
export function writeMapHistory(query: string, mode: "replace" | "push"): void {
  if (typeof window === "undefined") return;
  const url = `${window.location.pathname}${query}${window.location.hash}`;
  if (mode === "push") window.history.pushState(null, "", url);
  else window.history.replaceState(null, "", url);
}
