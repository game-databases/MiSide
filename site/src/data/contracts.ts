/*
 * SERVER-ONLY build-time readers over ../extracted.
 * Loaders here never import client components and nothing under src/data/
 * bundles into client JS — the browser sees only emitted public/ artifacts
 * (spec §2 rules).
 *
 * Every .jsonl dataset's FIRST line is a {"_meta": …} header (contracts
 * §Files); data rows follow one JSON object per line. The _meta line is
 * parsed and exposed, never skipped silently.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

/** Repo-root extracted/ (override for exotic checkouts; build runs with cwd=site). */
export function extractedRoot(): string {
  return (
    process.env.MISIDE_EXTRACTED_ROOT ?? join(process.cwd(), "..", "extracted")
  );
}

export interface JsonlFile<T> {
  meta: Record<string, unknown> | null;
  rows: T[];
}

/*
 * Two _meta header shapes exist in the corpus (measured 2026-08-25):
 *  • WRAPPED: {"_meta": {...}} — characters, cartridges, scenes, dialogue
 *    graphs, markers.
 *  • BARE: a header object as line 1 without the "_meta" key (carries
 *    build_id / derived_fields / schema keys instead) — documents family.
 * Files may also be EMPTY by contract (endings relink launch-member) or carry
 * no header at all (achievements/endings/dialogue data files, ledger files).
 */
function looksLikeHeader(obj: unknown, idField?: string): boolean {
  if (!obj || typeof obj !== "object") return false;
  const keys = Object.keys(obj as Record<string, unknown>);
  if (keys.includes("_meta")) return true;
  return (
    ["derived_fields", "schema", "schema_id", "generator"].some((k) =>
      keys.includes(k)
    ) && (!idField || !keys.includes(idField))
  );
}

/** Read a contract .jsonl file: header (any corpus shape) + typed rows. */
export function readJsonl<T>(relPath: string, idField?: string): JsonlFile<T> {
  let raw: string;
  try {
    raw = readFileSync(join(extractedRoot(), relPath), "utf8");
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      // empty-by-contract file (e.g. endings relink launch member)
      return { meta: null, rows: [] };
    }
    throw err;
  }
  const lines = raw.split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return { meta: null, rows: [] };
  let meta: Record<string, unknown> | null = null;
  let start = 0;
  const first = JSON.parse(lines[0]) as Record<string, unknown>;
  if (looksLikeHeader(first, idField)) {
    meta =
      first._meta !== undefined
        ? (first._meta as Record<string, unknown>)
        : first;
    start = 1;
  }
  const rows = lines.slice(start).map((l) => JSON.parse(l) as T);
  // Contract row-count pin: declared count must equal the data-row count.
  const declared = meta && typeof meta.row_count === "number" ? meta.row_count : null;
  if (declared !== null && declared !== rows.length) {
    throw new Error(
      `${relPath}: _meta.row_count=${declared} but ${rows.length} data rows`
    );
  }
  return { meta, rows };
}

/* ------------------------------------------------------------------ */
/* Dataset row types — only the fields the scaffold consumes.          */
/* Full schemas live in contracts/dataset-*.mdx; readers never invent  */
/* fallbacks or re-derive fields.                                      */
/* ------------------------------------------------------------------ */

export interface LocPointer {
  category: string;
  line_index: number;
}

export interface PersonageRow {
  character_id: string;
  kind: "mita" | "player";
  status: string;
  resource_path: string;
  save_key: string;
  name_loc: LocPointer;
  description_loc: LocPointer;
  palette_color1: number[];
  palette_color2: number[];
  name_is_shared: boolean;
  gallery_order: number;
  name_en: string;
  build_id: string;
  version_label: string;
}

export interface CartridgeRow {
  cartridge_id: string;
  family: "character" | "player";
  status: string;
  save_key: string;
  depicts_character_id: string | null;
  contains_player_id: string | null;
  collectible_set: string | null;
  container_location_binding: string | null;
  pickup_ref: { container: string; [k: string]: unknown } | null;
  build_id: string;
  version_label: string;
}

export interface MinigameRow {
  minigame_id: string;
  client_key: string;
  access_medium: string;
  community_alias: { alias: string; source: string } | null;
  name_loc: LocPointer | null;
  scoring_derivable: boolean;
  present_but_unreachable: boolean;
  achievement_ids: string[];
  unlocks_outfits: string[];
  build_id: string;
  version_label: string;
}

export interface AchievementRow {
  achievement_id: string;
  registry_index: number;
  display: Record<string, { name: string; category: string; line_index: number }>;
  icon: { status: string; official_url?: string | null };
  type_tag: string;
  joins: { ending_id: string | null; collectible_set: string | null };
  steam: { global_percent: number | null };
  flags: { get_bool_trusted: boolean };
  build_id: string;
}

export interface EndingRow {
  ending_id: string;
  kind: "ending" | "mode-stub";
  display_name_loc: LocPointer | null;
  achievement_id: string | null;
  mode_unlocked: { mode_id: string; state: string } | null;
  windows: unknown[];
  conditions: unknown[];
  award_chain_status: string | null;
  evidence: unknown[];
  notes_community: string | null;
  build_id: string;
}

export interface ProfileDocumentRow {
  document_id: string;
  family: "profile";
  subject_character_id: string;
  flash_save_key: string | null;
  placement_mechanism: string;
  name_loc: LocPointer;
  lore_loc: LocPointer;
  name_en: string;
  name_is_shared: boolean;
  achievement_sets: string[];
  build_id: string;
}

export interface WorldDocumentRow {
  document_id: string;
  family: "note" | "paper_part" | "novella_surface";
  carrier: { container: string; dump_file: string; mb_class: string; path_id: number };
  puzzle_index: number | null;
  text_mechanism: string;
  build_id: string;
}

export interface BookRow {
  book_id: string;
  consumer_scene: string;
  art_per_locale: Record<string, boolean>;
  locales_missing: string[];
  art_per_locale_available_count: number;
  build_id: string;
}

export interface SceneRow {
  scene_id: string;
  role: "story" | "boot" | "title" | "menu" | "unbound";
  location_id: string | null;
  objective_hints: LocPointer[];
  chapter_name_loc: LocPointer | null;
  spawn:
    | { x: number; y: number; z: number; source: "inline"; space: "world-assumed" }
    | null;
  build_id: string;
}

export interface PoiRow {
  poi_id: string;
  class: string;
  kind: string;
  level: string;
  location_id: string | null;
  position: {
    source: "inline" | "pptr-unresolved" | "none";
    space?: string;
    x?: number;
    y?: number;
    z?: number;
    points?: Array<Record<string, number>>;
    target?: unknown;
  };
  joins: Record<string, unknown>;
  build_id: string;
}

export interface MarkerRow {
  entity_kind: string;
  entity_slug: string;
  scene_id: string;
  x: number;
  y: number;
  [k: string]: unknown;
}

/* ------------------------------------------------------------------ */
/* Kind registry — the routed entity kinds with their id columns       */
/* (AC S6: generateStaticParams output == owning contract id column).  */
/* ------------------------------------------------------------------ */

export interface EntityKindDef {
  /** URL kind segment. */
  kind: string;
  /** Contract-relative jsonl path under extracted/data/. */
  file: string;
  /** The pinned id column. */
  idField: string;
  filter?: (row: unknown) => boolean;
}

export const ENTITY_KINDS: Record<string, EntityKindDef> = {
  mita: {
    kind: "mita",
    file: "data/characters/personages.jsonl",
    idField: "character_id",
    filter: (r) => (r as PersonageRow).kind === "mita",
  },
  players: {
    kind: "players",
    file: "data/characters/personages.jsonl",
    idField: "character_id",
    filter: (r) => (r as PersonageRow).kind === "player",
  },
  cartridges: {
    kind: "cartridges",
    file: "data/cartridges/cartridges.jsonl",
    idField: "cartridge_id",
  },
  minigames: {
    kind: "minigames",
    file: "data/cartridges/minigames.jsonl",
    idField: "minigame_id",
  },
  achievements: {
    kind: "achievements",
    file: "data/achievements/achievements.jsonl",
    idField: "achievement_id",
  },
  endings: {
    kind: "endings",
    file: "data/endings/endings.jsonl",
    idField: "ending_id",
  },
  profiles: {
    kind: "profiles",
    file: "data/documents/profile_documents.jsonl",
    idField: "document_id",
  },
  lore: {
    kind: "lore",
    file: "data/documents/world_documents.jsonl",
    idField: "document_id",
    filter: (r) =>
      ["paper_part", "novella_surface"].includes((r as WorldDocumentRow).family),
  },
  books: {
    kind: "books",
    file: "data/documents/books.jsonl",
    idField: "book_id",
  },
  locations: {
    kind: "locations",
    file: "data/scenes/scenes.jsonl",
    idField: "scene_id",
  },
};

/** Rows for a routed kind, honoring its pinned filter. */
export function kindRows(kind: string): unknown[] {
  const def = ENTITY_KINDS[kind];
  if (!def) throw new Error(`Unknown entity kind: ${kind}`);
  const { rows } = readJsonl<Record<string, unknown>>(def.file, def.idField);
  return def.filter ? rows.filter(def.filter) : rows;
}

/** AC S6 param source: exactly the contract id column, full diff — never sampled. */
export function kindIds(kind: string): string[] {
  const def = ENTITY_KINDS[kind];
  return kindRows(kind).map(
    (r) => String((r as Record<string, unknown>)[def.idField])
  );
}

export function findRow(kind: string, id: string): Record<string, unknown> | undefined {
  return (
    (kindRows(kind).find(
      (r) => String((r as Record<string, unknown>)[ENTITY_KINDS[kind].idField]) === id
    ) as Record<string, unknown>) ?? undefined
  );
}

/* Convenience singletons */
export function personages(): PersonageRow[] {
  return readJsonl<PersonageRow>("data/characters/personages.jsonl", "character_id").rows;
}
export function scenes(): SceneRow[] {
  return readJsonl<SceneRow>("data/scenes/scenes.jsonl", "scene_id").rows;
}

/* Shipped relink rows (extracted/relinks/) — modules join ONLY these; the
   site never derives an edge the corpus does not pin (AGENTS.md rule 8). */

/** Forward character→achievement membership (relink family
    character--achievement; mechanism/status ride the row). */
export interface CharacterAchievementEdge {
  from: string;
  achievement_id: string;
  mechanism: string;
  status: string;
}

export function characterAchievementEdges(): CharacterAchievementEdge[] {
  const { rows } = readJsonl<{
    direction?: string;
    from?: string | null;
    to?: string | null;
    mechanism?: string;
    status?: string;
  }>("relinks/character--achievement.jsonl");
  return rows
    .filter(
      (r) =>
        r.direction === "forward" &&
        typeof r.from === "string" &&
        typeof r.to === "string" &&
        r.to.startsWith("achievement:")
    )
    .map((r) => ({
      from: r.from as string,
      achievement_id: (r.to as string).slice("achievement:".length),
      mechanism: r.mechanism ?? "",
      status: r.status ?? "",
    }));
}

/** Forward character→scene membership (relink family
    character--scene-membership); null-from partials stay out. */
export interface CharacterSceneEdge {
  from: string;
  scene_id: string;
  status: string;
}

export function characterSceneEdges(): CharacterSceneEdge[] {
  const { rows } = readJsonl<{
    direction?: string;
    from?: string | null;
    to?: string | null;
    status?: string;
  }>("relinks/character--scene-membership.jsonl");
  return rows
    .filter(
      (r) =>
        r.direction === "forward" &&
        typeof r.from === "string" &&
        typeof r.to === "string" &&
        r.to.startsWith("scene:")
    )
    .map((r) => ({
      from: r.from as string,
      scene_id: (r.to as string).slice("scene:".length),
      status: r.status ?? "",
    }));
}
/** Minigame ids carried by one scene container (relink family
    minigame--scene-carrier, inverse direction): rows the corpus pins as
    "<Name>Class<" co-presence in that container's own asset list. Keyed
    "scene-class-family@<container>"; unknown containers return []. */
export function minigamesInContainer(container: string): string[] {
  const { rows } = readJsonl<{
    direction?: string;
    from?: string | null;
    to?: string | null;
  }>("relinks/minigame--scene-carrier.jsonl");
  const ids = new Set<string>();
  for (const r of rows) {
    if (
      r.direction === "inverse" &&
      r.from === `scene-class-family@${container}` &&
      typeof r.to === "string" &&
      r.to.startsWith("minigame:")
    ) {
      ids.add(r.to.slice("minigame:".length));
    }
  }
  return [...ids].sort();
}

export function poi(): PoiRow[] {
  return readJsonl<PoiRow>("data/scenes/poi.jsonl", "poi_id").rows;
}
export function markers(): MarkerRow[] {
  return readJsonl<MarkerRow>("data/scenes/markers.jsonl", "entity_kind").rows;
}
export function dialogueLevels(): string[] {
  // graphs/<level>.json — 19 carrier levels (dialogue contract §Files).
  // Node records key on `id` ("<container>:<Class>#<truePathID>", contract
  // §Identity scheme).
  const { rows } = readJsonl<{ id: string }>("data/dialogue/nodes.jsonl", "id");
  const levels = new Set<string>();
  for (const r of rows) levels.add(r.id.split(":")[0]);
  return [...levels].sort();
}
export function buildId(): string {
  const { meta } = readJsonl<unknown>("data/scenes/scenes.jsonl");
  const pins = (meta?.build_pins ?? meta?.pins) as
    | { buildId?: string; build_id?: string }
    | undefined;
  const id =
    (pins?.buildId as string) ??
    (pins?.build_id as string) ??
    (meta?.build_id as string);
  if (!id) throw new Error("No buildId pin found in dataset _meta headers");
  return id;
}
