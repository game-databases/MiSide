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
// Leaf reader lives in ./jsonl.ts so the joins registry reader (joins.ts)
// sits on ONE copy of the loader — re-exported here for API stability.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { extractedRoot, readJsonl } from "./jsonl.ts";

export { extractedRoot, readJsonl } from "./jsonl.ts";
export type { JsonlFile } from "./jsonl.ts";

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

/*
 * Marker row v2 (map-viewer spec §4.1): one shape, two sources.
 *  • poi-anchored rows carry the corpus-verbatim `poi_id` instance anchor.
 *  • placement-sourced rows (DS-5 profiles, minigame carriers) carry
 *    `poi_id: null` and are scene-granular FOREVER until S9 resolves carrier
 *    transforms — they never plot as pins.
 * `position.status` is the honesty axis: "projected" rows must agree with
 * projectedCoordinates() (AC MV-2); every other status renders designed
 * non-pin states. The emitter writes final `links.*` segments so this module
 * formats URLs, never maps vocabularies.
 */
export type MarkerPositionStatus =
  | "projected"
  | "awaiting-transform-stage"
  | "scene-granular";

export interface MarkerRow {
  marker_id: string;
  /** Instance anchor; null for placement-sourced rows. */
  poi_id: string | null;
  layer: string;
  /** poi-kind vocabulary — the chip/filter axis. */
  kind: string;
  /** ROUTED ENTITY_KINDS key (cartridges/profiles/…), not the poi family. */
  entity_kind: string;
  entity_slug: string;
  icon: { source: string | null; fallback_state: string };
  position: {
    x: number | null;
    y: number | null;
    z: number | null;
    status: MarkerPositionStatus;
    target?: unknown;
  };
  /** Provenance carried verbatim for the PinPopover provenance cell. */
  placement?: {
    mechanism?: string;
    source_join?: string;
    scene_binding?: string;
  };
  /** Required when one container hosts >1 controller/minigame (never 1-of-N). */
  instance_census?: Record<string, number>;
  links: { page_url: string | null; focus_url?: string };
}

/**
 * Normalized marker reader over data/scenes/markers.jsonl. Lenient on MISSING
 * OPTIONAL fields only — a row without a projecting position stays
 * non-projecting (fail-safe), it is never promoted. Zero data rows today
 * (no-orphan rule); M0's rerun fills the file without a schema change here.
 */
export function markers(): MarkerRow[] {
  return readJsonl<Partial<MarkerRow>>("data/scenes/markers.jsonl").rows.map(
    (raw): MarkerRow => {
      const pos = (raw.position ?? {}) as Record<string, unknown>;
      const x = typeof pos.x === "number" ? pos.x : null;
      const y = typeof pos.y === "number" ? pos.y : null;
      const z = typeof pos.z === "number" ? pos.z : null;
      const status =
        pos.status === "projected" ||
        pos.status === "awaiting-transform-stage" ||
        pos.status === "scene-granular"
          ? pos.status
          : // unknown/absent status can never plot — the pending register is
            // the honest ceiling for an unlabeled cell
            ("awaiting-transform-stage" as MarkerPositionStatus);
      const links = (raw.links ?? {}) as Record<string, unknown>;
      return {
        marker_id: String(raw.marker_id ?? raw.poi_id ?? raw.entity_slug ?? ""),
        poi_id: typeof raw.poi_id === "string" ? raw.poi_id : null,
        layer: String(raw.layer ?? ""),
        kind: String(raw.kind ?? ""),
        entity_kind: String(raw.entity_kind ?? ""),
        entity_slug: String(raw.entity_slug ?? ""),
        icon: {
          source:
            typeof (raw.icon as { source?: unknown })?.source === "string"
              ? ((raw.icon as { source: string }).source)
              : null,
          fallback_state:
            (raw.icon as { fallback_state?: string })?.fallback_state ??
            "named-explicit-missing",
        },
        position: {
          x,
          y,
          z,
          status,
          target: pos.target,
        },
        placement: (raw.placement ?? undefined) as MarkerRow["placement"],
        instance_census: (raw.instance_census ?? undefined) as
          | Record<string, number>
          | undefined,
        links: {
          page_url: typeof links.page_url === "string" ? links.page_url : null,
          focus_url:
            typeof links.focus_url === "string" ? links.focus_url : undefined,
        },
      };
    }
  );
}

/** The scene id a marker binds to (placement.scene_binding scalar first). */
export function markerSceneId(m: MarkerRow): string | null {
  if (m.placement?.scene_binding) return m.placement.scene_binding;
  if (!m.links.focus_url) return null;
  try {
    return new URLSearchParams(
      m.links.focus_url.slice(m.links.focus_url.indexOf("?"))
    ).get("scene");
  } catch {
    return null;
  }
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

/** Curated class→kind rulings (poi-kinds.json — plain JSON, not JSONL). */
export interface PoiKindRuling {
  class: string;
  kind: string;
  marker_eligible: boolean;
}

let poiKindsCache: PoiKindRuling[] | null = null;
export function poiKinds(): PoiKindRuling[] {
  if (!poiKindsCache) {
    const raw = readFileSync(
      join(extractedRoot(), "data", "scenes", "poi-kinds.json"),
      "utf8"
    );
    const doc = JSON.parse(raw) as { classes?: PoiKindRuling[] };
    poiKindsCache = Array.isArray(doc.classes) ? doc.classes : [];
  }
  return poiKindsCache;
}

/* Shipped relink rows (extracted/relinks/) — modules join ONLY these; the
   site never derives an edge the corpus does not pin (AGENTS.md rule 8).
   Every reader below is a thin typed view over ONE generic consumption path:
   joins.familyEdges(), which parses the file through the registry's own
   anchor grammar and census-gates against joins.json. Bespoke per-family
   loaders that could drift from the registry were the B-RP1 defect class. */
import { familyEdges } from "./joins.ts";

/** Forward character→achievement membership (relink family
    character--achievement; mechanism/status ride the row). */
export interface CharacterAchievementEdge {
  from: string;
  achievement_id: string;
  mechanism: string;
  status: string;
}

export function characterAchievementEdges(): CharacterAchievementEdge[] {
  return familyEdges("character--achievement")
    .filter(
      (e) =>
        e.direction === "forward" &&
        e.from?.raw != null &&
        e.to?.form === "achievement:"
    )
    .map((e) => ({
      from: e.from?.raw ?? "",
      achievement_id: e.to?.id ?? "",
      mechanism: e.mechanism ?? "",
      status: e.status ?? "",
    }));
}

/** Forward character→scene membership (relink family
    character--scene-membership); null-from partials stay out. */
export interface CharacterSceneEdge {
  from: string;
  scene_id: string;
  /** Provenance carry law (map-viewer §7): surfaced when !== "hard". */
  mechanism: string;
  status: string;
}

export function characterSceneEdges(): CharacterSceneEdge[] {
  return familyEdges("character--scene-membership")
    .filter(
      (e) =>
        e.direction === "forward" &&
        e.from?.raw != null &&
        e.to?.form === "scene:"
    )
    .map((e) => ({
      from: e.from?.raw ?? "",
      scene_id: e.to?.id ?? "",
      // provenance carry law (map-viewer §7 F-7): mechanism rides through to
      // render — surfaced whenever it is not "hard"
      mechanism: e.mechanism ?? "",
      status: e.status ?? "",
    }));
}

/**
 * Forward document→container membership (relink family
 * document--scene-membership): note/paper_part/novella_surface/
 * profile_document rows keyed "<family>:<id>" → "container:<level>".
 * The M4 books/lore scene source (map-viewer §7) — consumed, never derived.
 */
export interface DocumentSceneEdge {
  family: string;
  document_id: string;
  container: string;
  mechanism: string;
  status: string;
}

export function documentSceneEdges(): DocumentSceneEdge[] {
  return familyEdges("document--scene-membership")
    .filter(
      (e) =>
        e.direction === "forward" &&
        e.from?.raw != null &&
        e.from.form !== "<bare>" &&
        e.to?.form === "container:"
    )
    .map((e) => ({
      family: e.from!.form.slice(0, -1),
      document_id: e.from!.id,
      container: e.to!.id,
      mechanism: e.mechanism ?? "",
      status: e.status ?? "",
    }));
}

/**
 * Forward minigame→carrier edges (relink family minigame--scene-carrier):
 * "minigame:<id>" → "scene-class-family@<container>", emitter-split scalar
 * container on the row. The M4 minigame scene source (map-viewer §7).
 */
export interface MinigameCarrierEdge {
  minigame_id: string;
  container: string;
  mechanism: string;
  status: string;
}

const SCENE_CLASS_FAMILY = "scene-class-family@";

export function minigameCarrierEdges(): MinigameCarrierEdge[] {
  return familyEdges("minigame--scene-carrier")
    .filter(
      (e) =>
        e.direction === "forward" &&
        e.from?.form === "minigame:" &&
        e.to?.raw != null &&
        e.to.raw.startsWith(SCENE_CLASS_FAMILY)
    )
    .map((e) => ({
      minigame_id: e.from!.id,
      container: (e.to!.raw as string).slice(SCENE_CLASS_FAMILY.length),
      mechanism: e.mechanism ?? "",
      status: e.status ?? "",
    }));
}
/** Minigame ids carried by one scene container (relink family
    minigame--scene-carrier, inverse direction): rows the corpus pins as
    "<Name>Class<" co-presence in that container's own asset list. Keyed
    "scene-class-family@<container>"; unknown containers return []. */
export function minigamesInContainer(container: string): string[] {
  const ids = new Set<string>();
  for (const e of familyEdges("minigame--scene-carrier")) {
    if (
      e.direction === "inverse" &&
      e.from?.raw === `${SCENE_CLASS_FAMILY}${container}` &&
      e.to?.form === "minigame:"
    ) {
      ids.add(e.to.id);
    }
  }
  return [...ids].sort();
}

/**
 * save_key → cartridge row — the owning dataset's own identity column
 * (cartridges contract DS-4). The `flashes:<save_key>` anchor form of the
 * character--cartridge join resolves THROUGH this index and never through a
 * guessed nameSave equality; an unknown save_key is an orphan (no link).
 */
let cartridgeSaveKeyIndex: Map<string, CartridgeRow> | null = null;
export function cartridgeBySaveKey(): Map<string, CartridgeRow> {
  if (!cartridgeSaveKeyIndex) {
    cartridgeSaveKeyIndex = new Map(
      kindRows("cartridges").map((r) => {
        const c = r as unknown as CartridgeRow;
        return [c.save_key, c];
      })
    );
  }
  return cartridgeSaveKeyIndex;
}

export function poi(): PoiRow[] {
  return readJsonl<PoiRow>("data/scenes/poi.jsonl", "poi_id").rows;
}
/** Carrier level → node count (one read; search text + transcript census). */
export function dialogueLevelNodeCounts(): Map<string, number> {
  // graphs/<level>.json — 19 carrier levels (dialogue contract §Files).
  // Node records key on `id` ("<container>:<Class>#<truePathID>", contract
  // §Identity scheme).
  const { rows } = readJsonl<{ id: string }>("data/dialogue/nodes.jsonl", "id");
  const counts = new Map<string, number>();
  for (const r of rows) {
    const lvl = r.id.split(":")[0];
    counts.set(lvl, (counts.get(lvl) ?? 0) + 1);
  }
  return counts;
}
export function dialogueLevels(): string[] {
  return [...dialogueLevelNodeCounts().keys()].sort();
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
