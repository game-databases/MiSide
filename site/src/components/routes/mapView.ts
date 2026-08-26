/*
 * Server-side map view builders (shared by BOTH route trees — the single
 * place contract rows become viewer props). Everything here runs at build
 * time; the island receives plain JSON props and never fetches.
 *
 * Laws honored here:
 *  • markers come ONLY from markers() (markers.jsonl) — never from poi.jsonl,
 *    never from runtime DS-4/DS-5 joins (map-viewer §4 forbidden list);
 *  • plotting goes through projectedCoordinates()/markerCoordinates() only;
 *  • labels ride the filler chain: localized chapter name → re-spaced id
 *    (desluggedLabel) — no invented names (CH-6);
 *  • bounds stay null until the calibration rerun writes them; null is the
 *    honest value, never a bounding guess (OQ-6).
 */
import {
  ENTITY_KINDS,
  findRow,
  markerSceneId,
  markers,
  poiKinds,
  poi,
  scenes,
  type MarkerRow,
  type PoiRow,
} from "@/data/contracts";
import { resolveLoc } from "@/data/resolveLoc";
import { desluggedLabel, displayName } from "./entityDisplay";
import { markerCoordinates } from "@/components/map/projection";
import type {
  MapCellVM,
  MapChromeStrings,
  MapPinVM,
  SceneEntryVM,
  SceneMarkersVM,
  SwitcherGroup,
} from "@/components/map/viewTypes";

const ROLE_ORDER = ["boot", "title", "menu", "unbound"] as const;

/** Locale-prefixed href for an emitter-written root-relative path. */
function prefixed(
  prefix: string,
  path: string | null | undefined
): string | null {
  if (!path) return null;
  return `${prefix}${path}`;
}

/** Popover/list title: the owning entity's own name in THIS locale. */
function markerTitle(m: MarkerRow, localeCode: string): string {
  const def = ENTITY_KINDS[m.entity_kind];
  if (def) {
    const row = findRow(m.entity_kind, m.entity_slug);
    if (row) return displayName(m.entity_kind, row, localeCode);
  }
  // orphan-guarded fallback: re-spaced slug, never an invented name
  return desluggedLabel(m.entity_slug) || m.entity_slug;
}

function pinVM(
  m: MarkerRow,
  coords: { x: number; y: number },
  prefix: string,
  localeCode: string
): MapPinVM {
  return {
    markerId: m.marker_id,
    kind: m.kind,
    title: markerTitle(m, localeCode),
    x: coords.x,
    y: coords.y,
    entityKey: `${m.entity_kind}:${m.entity_slug}`,
    pageHref: prefixed(prefix, m.links.page_url),
    focusHref: prefixed(prefix, m.links.focus_url ?? null),
    mechanism: m.placement?.mechanism,
    sourceJoin: m.placement?.source_join,
  };
}

function cellVM(
  m: MarkerRow,
  status: "awaiting-transform-stage" | "scene-granular",
  prefix: string,
  localeCode: string
): MapCellVM {
  return {
    markerId: m.marker_id,
    kind: m.kind,
    status,
    title: markerTitle(m, localeCode),
    entityKey: `${m.entity_kind}:${m.entity_slug}`,
    pageHref: prefixed(prefix, m.links.page_url),
    focusHref: prefixed(prefix, m.links.focus_url ?? null),
    mechanism: m.placement?.mechanism,
    sourceJoin: m.placement?.source_join,
    instanceCensus: m.instance_census,
  };
}

const byTitle = (a: { title: string }, b: { title: string }) =>
  a.title.localeCompare(b.title);

/** Partition one scene's marker rows into plotted pins + non-pin cells. */
export function sceneMarkers(
  sceneId: string,
  localePrefix: string,
  localeCode: string
): SceneMarkersVM {
  const out: SceneMarkersVM = { pins: [], pending: [], granular: [] };
  for (const m of markers()) {
    if (markerSceneId(m) !== sceneId) continue;
    const coords = markerCoordinates(m.position);
    if (coords) {
      out.pins.push(pinVM(m, coords, localePrefix, localeCode));
    } else if (m.position.status === "scene-granular") {
      out.granular.push(cellVM(m, "scene-granular", localePrefix, localeCode));
    } else {
      // awaiting-transform-stage — and any disagreement row, which may never
      // plot (fail-safe ceiling below the emitted claim)
      out.pending.push(
        cellVM(m, "awaiting-transform-stage", localePrefix, localeCode)
      );
    }
  }
  out.pins.sort(byTitle);
  out.pending.sort(byTitle);
  out.granular.sort(byTitle);
  return out;
}

/** Registry v2 rows as the viewer consumes them (additive over v1 fields). */
export function registryEntries(localeCode: string): SceneEntryVM[] {
  return scenes().map((s) => ({
    scene_id: s.scene_id,
    role: s.role,
    label:
      (s.chapter_name_loc ? resolveLoc(localeCode, s.chapter_name_loc) : "") ||
      desluggedLabel(s.scene_id),
    // bounds settle at the S9/P5 calibration rerun; null stays honest
    bounds: null,
    zoom: [1, 4] as [number, number],
    status: "awaiting-artwork" as const,
  }));
}

/**
 * Switcher groups (map-viewer §5): story scenes grouped by chapter pointer
 * order; chapters missing on a story level group as unlabeled (never a
 * guessed chapter); boot/title/menu/unbound keep their role tokens in the
 * machine-voice register.
 */
export function switcherGroups(
  localeCode: string,
  chromeChapterUnlabeled: string
): SwitcherGroup[] {
  const entries = registryEntries(localeCode);
  const groups = new Map<string, SwitcherGroup>();

  const chapterLine = new Map<string, number | null>();
  for (const s of scenes()) {
    chapterLine.set(s.scene_id, s.chapter_name_loc?.line_index ?? null);
  }

  for (const e of entries) {
    if (e.role === "story") {
      const line = chapterLine.get(e.scene_id);
      const key = line !== null && line !== undefined ? `chapter:${line}` : "unlabeled";
      let g = groups.get(key);
      if (!g) {
        g = {
          id: key,
          label: key === "unlabeled" ? chromeChapterUnlabeled : e.label,
          lcd: false,
          scenes: [],
        };
        groups.set(key, g);
      }
      g.scenes.push(e);
    } else {
      let g = groups.get(e.role);
      if (!g) {
        g = { id: e.role, label: e.role, lcd: true, scenes: [] };
        groups.set(e.role, g);
      }
      g.scenes.push(e);
    }
  }

  const bySceneId = (a: SceneEntryVM, b: SceneEntryVM) =>
    a.scene_id.localeCompare(b.scene_id, undefined, { numeric: true });

  const chapterGroups = [...groups.entries()]
    .filter(([id]) => id.startsWith("chapter:"))
    .sort(([a], [b]) => Number(a.slice("chapter:".length)) - Number(b.slice("chapter:".length)))
    .map(([, g]) => ({ ...g, scenes: [...g.scenes].sort(bySceneId) }));
  const unlabeledGroup = groups.get("unlabeled");
  const roleGroups = ROLE_ORDER.filter((r) => groups.has(r)).map((r) => ({
    ...(groups.get(r) as SwitcherGroup),
    scenes: [...(groups.get(r) as SwitcherGroup).scenes].sort(bySceneId),
  }));
  return [
    ...chapterGroups,
    ...(unlabeledGroup
      ? [{ ...unlabeledGroup, scenes: [...unlabeledGroup.scenes].sort(bySceneId) }]
      : []),
    ...roleGroups,
  ];
}

/** Default scene: first entry of the switcher order — deterministic. */
export function defaultSceneId(
  localeCode: string,
  chromeChapterUnlabeled: string
): string {
  const groups = switcherGroups(localeCode, chromeChapterUnlabeled);
  for (const g of groups) {
    if (g.scenes[0]) return g.scenes[0].scene_id;
  }
  return scenes()[0]?.scene_id ?? "";
}

/**
 * Per-scene marker partition for EVERY scene at once (one read of
 * markers.jsonl for the /map shell instead of 24).
 */
export function markersByScene(
  localePrefix: string,
  localeCode: string
): Record<string, SceneMarkersVM> {
  const out: Record<string, SceneMarkersVM> = {};
  for (const s of scenes())
    out[s.scene_id] = { pins: [], pending: [], granular: [] };
  for (const m of markers()) {
    const sid = markerSceneId(m);
    if (!sid || !out[sid]) continue;
    const coords = markerCoordinates(m.position);
    if (coords) out[sid].pins.push(pinVM(m, coords, localePrefix, localeCode));
    else if (m.position.status === "scene-granular")
      out[sid].granular.push(
        cellVM(m, "scene-granular", localePrefix, localeCode)
      );
    else
      out[sid].pending.push(
        cellVM(m, "awaiting-transform-stage", localePrefix, localeCode)
      );
  }
  for (const vm of Object.values(out)) {
    vm.pins.sort(byTitle);
    vm.pending.sort(byTitle);
    vm.granular.sort(byTitle);
  }
  return out;
}

/* ------------------------------------------------------------------ */
/* /locations/[scene_id] server modules                                */
/* ------------------------------------------------------------------ */

export interface PoiClassEntry {
  /** Class-preserving label via desluggedLabel — never an invented noun. */
  label: string;
  cls: string;
  /** Instance count when the class hosts >1 row (never silently 1-of-N). */
  count: number;
}

export interface PoiListingKindGroup {
  kind: string;
  eligible: boolean;
  classes: PoiClassEntry[];
}

/**
 * The scene POI listing (list form) from poi.jsonl grouped by kind —
 * eligible kinds render their classes with instance counts; ineligible
 * classes surface as counted rows only (the honesty ledger, map-viewer §7).
 */
export function scenePoiListing(sceneId: string): PoiListingKindGroup[] {
  const ruling = new Map(poiKinds().map((k) => [k.class, k]));
  const eligibleByKind = new Map<string, Map<string, number>>();
  const ineligibleByKind = new Map<string, Map<string, number>>();
  for (const r of poi().filter((p: PoiRow) => p.level === sceneId)) {
    const rule = ruling.get(r.class);
    const target =
      rule?.marker_eligible === true ? eligibleByKind : ineligibleByKind;
    const kind = rule?.kind ?? r.kind;
    let classes = target.get(kind);
    if (!classes) {
      classes = new Map();
      target.set(kind, classes);
    }
    classes.set(r.class, (classes.get(r.class) ?? 0) + 1);
  }
  const groups: PoiListingKindGroup[] = [];
  const pushAll = (
    src: Map<string, Map<string, number>>,
    eligible: boolean
  ) => {
    for (const [kind, classes] of src) {
      groups.push({
        kind,
        eligible,
        classes: [...classes.entries()]
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([cls, n]) => ({ cls, label: desluggedLabel(cls), count: n })),
      });
    }
  };
  pushAll(eligibleByKind, true);
  pushAll(ineligibleByKind, false);
  return groups.sort((a, b) =>
    a.eligible !== b.eligible
      ? a.eligible
        ? -1
        : 1
      : a.kind.localeCompare(b.kind)
  );
}

/** Objective-hint lines resolved for THIS locale (empty → caller omits). */
export function sceneObjectiveHints(
  sceneId: string,
  localeCode: string
): string[] {
  const row = scenes().find((s) => s.scene_id === sceneId);
  if (!row) return [];
  return row.objective_hints
    .map((p) => resolveLoc(localeCode, p))
    .filter((t) => t.length > 0);
}

/** Scene display label through the filler chain (locations pages reuse it). */
export function sceneLabel(sceneId: string, localeCode: string): string {
  const row = scenes().find((s) => s.scene_id === sceneId);
  if (!row) return sceneId;
  return (
    (row.chapter_name_loc ? resolveLoc(localeCode, row.chapter_name_loc) : "") ||
    desluggedLabel(row.scene_id)
  );
}

/**
 * The map.* chrome subset the viewer island needs, extracted once — both
 * route trees pass it through unchanged.
 */
export function mapChromeStrings(chrome: Record<string, string>): MapChromeStrings {
  return {
    scenes: chrome["map.scenes"],
    sceneLocked: chrome["map.sceneLocked"],
    showAll: chrome["map.showAll"],
    hideAll: chrome["map.hideAll"],
    resetView: chrome["map.resetView"],
    filterSearch: chrome["map.filterSearch"],
    resultsCount: chrome["map.resultsCount"],
    awaitingTransform: chrome["map.awaitingTransform"],
    sceneGranular: chrome["map.sceneGranular"],
    unplaced: chrome["map.unplaced"],
    openPage: chrome["map.popover.openPage"],
    close: chrome["map.popover.close"],
    zoomIn: chrome["map.zoomIn"],
    zoomOut: chrome["map.zoomOut"],
    chapterUnlabeled: chrome["map.chapterUnlabeled"],
  };
}
