/*
 * Plain, serializable view models passed from the server builders
 * (routes/mapView.ts) into the client island. Nothing under components/map
 * may import src/data readers directly — the browser sees only these props.
 */

import type { MarkerPositionStatus } from "@/data/contracts";

/** One plotted pin (position.status === "projected" AND projecting floats). */
export interface MapPinVM {
  markerId: string;
  kind: string;
  title: string;
  x: number;
  y: number;
  /** "<routed_entity_kind>:<slug>" — the URL-focus join key. */
  entityKey: string;
  /** Crawlable entity anchor (emitter-written path, locale-prefixed). */
  pageHref: string | null;
  /** Deep link back into the viewer (emitter-written, locale-prefixed). */
  focusHref: string | null;
  mechanism?: string;
  /** Relink edge status verbatim (§5 carry-law OR leg: status !== "modeled"). */
  relinkStatus?: string;
  sourceJoin?: string;
}

/**
 * Non-plotted marker rows: awaiting-transform-stage and scene-granular.
 * They render as list chips beside the map (and, once imagery + bounds
 * exist, as visible-locked cells) — never at faked coordinates.
 */
export interface MapCellVM {
  markerId: string;
  kind: string;
  status: Extract<MarkerPositionStatus, "awaiting-transform-stage" | "scene-granular">;
  title: string;
  /** "<routed_entity_kind>:<slug>" — the URL-focus join key. */
  entityKey: string;
  pageHref: string | null;
  focusHref: string | null;
  mechanism?: string;
  /** Relink edge status verbatim (§5 carry-law OR leg: status !== "modeled"). */
  relinkStatus?: string;
  sourceJoin?: string;
  /** Present when a container hosts >1 controller/minigame (never 1-of-N). */
  instanceCensus?: Record<string, number>;
}

export interface SceneMarkersVM {
  pins: MapPinVM[];
  pending: MapCellVM[];
  granular: MapCellVM[];
}

export type SceneStatus = "awaiting-artwork" | "ready";

/** One registry row as the viewer consumes it (map-viewer §3.2d shapes). */
export interface SceneEntryVM {
  scene_id: string;
  role: string;
  /** Filler-chain display label: localized chapter name → re-spaced id. */
  label: string;
  bounds: [number, number, number, number] | null;
  zoom: [number, number];
  status: SceneStatus;
}

export interface SwitcherGroup {
  /** Stable key; "chapter:<line>" for story chapters, role for the rest. */
  id: string;
  /** Rendered group heading; role groups stay machine-voice (LCD). */
  label: string;
  /** Role-token groups render in the LCD register, localized ones do not. */
  lcd: boolean;
  scenes: SceneEntryVM[];
}

/** Minimal chrome subset the island needs (strings resolved server-side). */
export interface MapChromeStrings {
  scenes: string;
  sceneLocked: string;
  showAll: string;
  hideAll: string;
  resetView: string;
  filterSearch: string;
  resultsCount: string;
  awaitingTransform: string;
  sceneGranular: string;
  unplaced: string;
  openPage: string;
  close: string;
  zoomIn: string;
  zoomOut: string;
  chapterUnlabeled: string;
}
