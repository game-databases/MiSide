"use client";

import * as React from "react";

import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { cn } from "@/lib/utils";
import { buildMapSearch, parseMapState, writeMapHistory } from "./mapState";
import { KindFilter } from "./KindFilter";
import { PinPopover, type PopoverTarget } from "./PinPopover";
import { SceneMap } from "./SceneMap";
import { SceneSwitcher } from "./SceneSwitcher";
import type {
  MapCellVM,
  MapChromeStrings,
  MapPinVM,
  SceneMarkersVM,
  SwitcherGroup,
} from "./viewTypes";

/*
 * MapViewer — the /map interaction shell (map-viewer §5/§6) and the
 * scene-locked embed on /locations/[scene_id] (mode="locked").
 *
 * State law (A-MV1 OQ-5): replaceState for filter toggles, focus changes,
 * focus clear and ?kinds= edits; pushState ONLY on scene change so Back
 * walks the scene trail; cold load restores whatever the URL carries;
 * popstate re-syncs. Locked mode writes no history — the page owns the URL.
 *
 * Honest-state law: zero markers renders the explicit-missing well inside
 * SceneMap; absence prose is a defect (design-standard §5.1).
 */

const EMPTY_MARKERS: SceneMarkersVM = { pins: [], pending: [], granular: [] };

export interface MapViewerProps {
  mode: "full" | "locked";
  groups: SwitcherGroup[];
  /** Every scene id the switcher can address (validity gate for ?scene=). */
  sceneIds: string[];
  initialSceneId: string;
  markersByScene: Record<string, SceneMarkersVM>;
  /** Chrome strings resolved server-side (map.* namespace). */
  chromeStrings: MapChromeStrings;
  className?: string;
}

export function MapViewer({
  mode,
  groups,
  sceneIds,
  initialSceneId,
  markersByScene,
  chromeStrings,
  className,
}: MapViewerProps) {
  const [sceneId, setSceneId] = React.useState(initialSceneId);
  /** null = no explicit selection (every kind enabled); Set = enabled subset. */
  const [enabledKinds, setEnabledKinds] = React.useState<Set<string> | null>(
    null
  );
  const [focus, setFocus] = React.useState<{ kind: string; slug: string } | null>(
    null
  );
  const [query, setQuery] = React.useState("");
  const [hoveredKind, setHoveredKind] = React.useState<string | null>(null);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  // cold load restores whatever the URL carries (full mode only)
  React.useEffect(() => {
    if (mode !== "full") return;
    const st = parseMapState(new URLSearchParams(window.location.search));
    if (st.scene && sceneIds.includes(st.scene)) setSceneId(st.scene);
    if (st.kinds) setEnabledKinds(new Set(st.kinds));
    if (st.focus) setFocus({ kind: st.focus.kind, slug: st.focus.slug });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- cold load once
  }, []);

  // Back/forward walks the scene trail — re-sync from the URL, never rewrite.
  // F-MV4: FULL re-sync — a URL without a usable ?scene= restores the default
  // scene instead of stranding the select on whatever was open before Back.
  React.useEffect(() => {
    if (mode !== "full") return;
    const onPop = () => {
      const st = parseMapState(new URLSearchParams(window.location.search));
      setSceneId(
        st.scene && sceneIds.includes(st.scene) ? st.scene : initialSceneId
      );
      setEnabledKinds(st.kinds ? new Set(st.kinds) : null);
      setFocus(st.focus ? { kind: st.focus.kind, slug: st.focus.slug } : null);
      setSelectedId(null);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- resync law
  }, [mode, sceneIds, initialSceneId]);

  const vm = markersByScene[sceneId] ?? EMPTY_MARKERS;

  const kindChips = React.useMemo(() => {
    const counts = new Map<string, number>();
    for (const m of [...vm.pins, ...vm.pending, ...vm.granular])
      counts.set(m.kind, (counts.get(m.kind) ?? 0) + 1);
    return [...counts.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([kind, count]) => ({
        kind,
        count,
        enabled: !enabledKinds || enabledKinds.has(kind),
      }));
  }, [vm, enabledKinds]);

  const matchesQuery = React.useCallback(
    (title: string) =>
      query.trim().length === 0 ||
      title.toLowerCase().includes(query.trim().toLowerCase()),
    [query]
  );
  const isEnabled = React.useCallback(
    (kind: string) => !enabledKinds || enabledKinds.has(kind),
    [enabledKinds]
  );

  const visiblePins = React.useMemo(
    () =>
      vm.pins.filter((p) => isEnabled(p.kind) && matchesQuery(p.title)),
    [vm, isEnabled, matchesQuery]
  );
  // F-MV4 filter law: the kind toggles and the quicksearch gate EVERY
  // rendered row — plotted pins, deferred chips and the in-panel cells alike.
  // A row that is on screen is always a row that passes the filters.
  const visiblePending = React.useMemo(
    () =>
      vm.pending.filter((c) => isEnabled(c.kind) && matchesQuery(c.title)),
    [vm, isEnabled, matchesQuery]
  );
  const visibleGranular = React.useMemo(
    () =>
      vm.granular.filter((c) => isEnabled(c.kind) && matchesQuery(c.title)),
    [vm, isEnabled, matchesQuery]
  );

  const focusKey = focus ? `${focus.kind}:${focus.slug}` : null;
  const focusedRow = focusKey
    ? [...vm.pins, ...vm.pending, ...vm.granular].find(
        (m) => m.entityKey === focusKey
      )
    : undefined;
  const focusedMarkerId = focusedRow?.markerId ?? null;

  // --- history-law writers -------------------------------------------
  // canonical kinds order = the chip row's order (sorted vocabulary)
  const writeKinds = (next: Set<string> | null) => {
    setEnabledKinds(next);
    if (mode !== "full") return;
    const list =
      next === null
        ? null
        : kindChips.map((c) => c.kind).filter((k) => next.has(k));
    writeMapHistory(
      buildMapSearch(window.location.search, { kinds: list }),
      "replace"
    );
  };

  const selectScene = (next: string) => {
    if (next === sceneId) return;
    setSceneId(next);
    setSelectedId(null);
    if (mode !== "full") return;
    // the ONE pushState in the viewer — Back walks the scene trail
    writeMapHistory(
      buildMapSearch(window.location.search, { scene: next }),
      "push"
    );
  };

  const clearFocus = () => {
    setFocus(null);
    if (mode !== "full") return;
    writeMapHistory(
      buildMapSearch(window.location.search, { focus: null }),
      "replace"
    );
  };

  const onSelectPin = React.useCallback(
    (markerId: string) =>
      setSelectedId((cur) => (cur === markerId ? null : markerId)),
    []
  );
  const onClosePopover = React.useCallback(() => setSelectedId(null), []);
  const onPinHover = React.useCallback(
    (kind: string | null) => setHoveredKind(kind),
    []
  );

  const selectedTarget: PopoverTarget | null = React.useMemo(() => {
    if (!selectedId) return null;
    const pin = vm.pins.find((p) => p.markerId === selectedId);
    if (pin) return popoverFromPin(pin);
    const cell = [...vm.pending, ...vm.granular].find(
      (c) => c.markerId === selectedId
    );
    return cell ? popoverFromCell(cell) : null;
  }, [selectedId, vm]);

  // The quicksearch LCD speaks for what IS on screen — every disposition,
  // so "0 shown" can never contradict a visible list (F-MV4).
  const shownCount =
    visiblePins.length + visiblePending.length + visibleGranular.length;

  return (
    <div data-slot="map-viewer" className={cn("flex flex-col gap-3", className)}>
      {/* toolbar row 1 — scene trail control */}
      <div className="flex flex-wrap items-center gap-2">
        {mode === "full" && (
          <SceneSwitcher
            groups={groups}
            sceneId={sceneId}
            label={chromeStrings.scenes}
            onSelect={selectScene}
          />
        )}
        {mode === "locked" && (
          <LcdTerminal className="w-fit rounded-full px-4 py-1.5 text-sm">
            {chromeStrings.sceneLocked}
          </LcdTerminal>
        )}
        {focus && (
          // F-MV4 microcopy law: the chip prints the entity's own loc-correct
          // name (markerTitle); the raw `kind:slug` key stays on title/aria
          // only, as the machine-plane join.
          <button
            type="button"
            onClick={clearFocus}
            title={`${focus.kind}:${focus.slug}`}
            aria-label={`${focus.kind}:${focus.slug}`}
            className="inline-flex min-h-11 items-center gap-2 rounded-full bg-primary px-4 font-lcd text-xs uppercase tracking-wide text-primary-foreground shadow-glow-pulse hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span aria-hidden>*</span>
            {(focusedRow?.title ?? "").toUpperCase() ||
              `${focus.kind}:${focus.slug}`}
            <span aria-hidden className="text-base leading-none">
              ×
            </span>
          </button>
        )}
      </div>

      {/* toolbar row 2 — kind join + quicksearch (reactive, never a form) */}
      <div className="flex flex-col gap-2">
        <KindFilter
          kinds={kindChips}
          kindLabels={chromeStrings.kindLabels}
          hoveredKind={hoveredKind}
          onToggle={(k) => {
            let next: Set<string>;
            if (enabledKinds === null) {
              // first toggle starts an explicit selection: everything ON minus k
              next = new Set(kindChips.map((c) => c.kind));
              next.delete(k);
            } else {
              next = new Set(enabledKinds);
              if (next.has(k)) next.delete(k);
              else next.add(k);
            }
            writeKinds(next);
          }}
          onHover={onPinHover}
          onShowAll={() => writeKinds(null)}
          onHideAll={() => writeKinds(new Set())}
          showAllLabel={chromeStrings.showAll}
          hideAllLabel={chromeStrings.hideAll}
        />
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={chromeStrings.filterSearch}
            aria-label={chromeStrings.filterSearch}
            className="h-11 w-full max-w-xs flex-none rounded-full border border-border bg-secondary px-4 text-sm text-secondary-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex-1"
          />
          {query.trim().length > 0 && (
            <LcdTerminal className="w-fit rounded-full px-4 py-1.5 text-sm">
              {shownCount} {chromeStrings.resultsCount}
            </LcdTerminal>
          )}
        </div>
      </div>

      <SceneMap
        sceneId={sceneId}
        bounds={null /* registry bounds land with S9/P5 calibration */}
        zoom={[1, 4]}
        pins={visiblePins}
        pendingCells={visiblePending}
        granularCells={visibleGranular}
        pendingLabel={chromeStrings.awaitingTransform}
        granularLabel={chromeStrings.sceneGranular}
        focusedMarkerId={focusedMarkerId}
        hoveredKind={hoveredKind}
        popoverTarget={selectedTarget}
        popoverChrome={{
          awaitingTransform: chromeStrings.awaitingTransform,
          sceneGranular: chromeStrings.sceneGranular,
          openPage: chromeStrings.openPage,
          close: chromeStrings.close,
        }}
        popoverLabels={{
          kindLabels: chromeStrings.kindLabels,
          censusLabels: chromeStrings.censusLabels,
        }}
        controlLabels={{
          zoomIn: chromeStrings.zoomIn,
          zoomOut: chromeStrings.zoomOut,
          resetView: chromeStrings.resetView,
        }}
        onSelectPin={onSelectPin}
        onClosePopover={onClosePopover}
        onPinHover={onPinHover}
      />

      {/* F-MV4 one-row law: deferred rows render ONCE — as the in-panel
          LockedCell strip (SceneMap), whose cells are themselves the
          crawlable <a href> anchors (AC MV-4) with the popover on click.
          The old below-panel chip stack is gone; only PLOTTED pins keep a
          dedicated SSR anchor pill row here, since their markers live inside
          the Leaflet canvas where crawlers cannot see them. */}
      {visiblePins.length > 0 && (
        <ul className="flex flex-wrap gap-1.5">
          {visiblePins.map((p) =>
            p.pageHref ? (
              <li key={`anchor-${p.markerId}`}>
                <a
                  href={p.pageHref}
                  className="inline-block rounded-full bg-secondary px-3 py-1 font-lcd text-xs text-secondary-foreground hover:bg-accent"
                >
                  {p.title}
                </a>
              </li>
            ) : null
          )}
        </ul>
      )}
    </div>
  );
}

function popoverFromPin(pin: MapPinVM): PopoverTarget {
  return {
    markerId: pin.markerId,
    kind: pin.kind,
    title: pin.title,
    pageHref: pin.pageHref,
    mechanism: pin.mechanism,
    relinkStatus: pin.relinkStatus,
    sourceJoin: pin.sourceJoin,
    status: "projected",
  };
}

function popoverFromCell(cell: MapCellVM): PopoverTarget {
  return {
    markerId: cell.markerId,
    kind: cell.kind,
    title: cell.title,
    pageHref: cell.pageHref,
    mechanism: cell.mechanism,
    relinkStatus: cell.relinkStatus,
    sourceJoin: cell.sourceJoin,
    status: cell.status,
    instanceCensus: cell.instanceCensus,
  };
}
