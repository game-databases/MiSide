"use client";

import * as React from "react";
import type * as LType from "leaflet";

import { cn } from "@/lib/utils";
import { VoidWell } from "@/components/kit/VoidWell";
import { LockedCell } from "./LockedCell";
import { PinPopover, type PopoverTarget } from "./PinPopover";
import { kindPinStyle } from "./kindAxis";
import type { MapCellVM, MapPinVM } from "./viewTypes";

/*
 * SceneMap — the Leaflet island host (map-viewer §5). Island boundary
 * preserved: Leaflet loads ONLY here, dynamically, so no other route bundles
 * it (AC MV-8 bundle assert).
 *
 * Coordinate law (§4.2): plotted pixels come only from rows that pass
 * markerCoordinates()/projectedCoordinates() — the server partition already
 * guarantees it; this component plots the plain numbers it receives.
 * CRS.Simple plots raw world coords ([y, x]); fit-to-bounds activates only
 * when the registry carries bounds, until then the deterministic default
 * view centers on the MEAN of the plotted points (presentation math over
 * consumed rows — OQ-6 ruling).
 *
 * F-MV4 in-panel law: rows WITHOUT projecting coordinates are not hidden —
 * they render INSIDE the panel as a deterministic stacked LockedCell strip
 * over the grid's start edge. The strip is a list, not a map claim: fixed
 * offsets carry zero spatial meaning and never fake a coordinate. Every cell
 * opens the same PinPopover a pin does (provenance cell included), so the
 * detail layer is reachable on today's all-deferred corpus.
 *
 * Imagery law (OQ-2 progressive + §3.1 fence): authored schematics live at
 * public/map/<scene_id>/base.svg (+ optional meta.json anchors). An image is
 * overlaid ONLY when the registry carries calibrated bounds — uncalibrated
 * artwork would fake coordinates, which the emission fence forbids. Until
 * then the schematic grid IS the honest awaiting-artwork state.
 *
 * History law lives in MapViewer/mapState, never here.
 */

export interface SceneMapProps {
  sceneId: string;
  bounds: [number, number, number, number] | null;
  zoom: [number, number];
  pins: MapPinVM[];
  /** Non-plotted rows of THIS scene after the viewer's filters. */
  pendingCells: MapCellVM[];
  granularCells: MapCellVM[];
  pendingLabel: string;
  granularLabel: string;
  focusedMarkerId: string | null;
  hoveredKind: string | null;
  popoverTarget: PopoverTarget | null;
  popoverChrome: {
    awaitingTransform: string;
    sceneGranular: string;
    openPage: string;
    close: string;
  };
  popoverLabels?: {
    kindLabels?: Record<string, string>;
    censusLabels?: Record<string, string>;
  };
  /** Localized control labels (≥44 px pill controls, AC MV-7). */
  controlLabels: { zoomIn: string; zoomOut: string; resetView: string };
  onSelectPin: (markerId: string) => void;
  onClosePopover: () => void;
  onPinHover: (kind: string | null) => void;
  className?: string;
}

function cssProps(style: React.CSSProperties): string {
  return Object.entries(style)
    .filter(([, v]) => v !== undefined)
    .map(([k, v]) => `${k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())}:${String(v)}`)
    .join(";");
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

export function SceneMap(props: SceneMapProps) {
  const {
    sceneId,
    bounds,
    zoom,
    pins,
    pendingCells,
    granularCells,
    pendingLabel,
    granularLabel,
    focusedMarkerId,
    hoveredKind,
    popoverTarget,
    popoverChrome,
    popoverLabels,
    controlLabels,
    onSelectPin,
    onClosePopover,
    onPinHover,
    className,
  } = props;

  const hostRef = React.useRef<HTMLDivElement | null>(null);
  const mapRef = React.useRef<LType.Map | null>(null);
  const pinLayerRef = React.useRef<LType.LayerGroup | null>(null);
  const imageryRef = React.useRef<LType.ImageOverlay | null>(null);
  const anchorRef = React.useRef<HTMLDivElement | null>(null);
  const [mapReady, setMapReady] = React.useState(0);
  const [imageryReady, setImageryReady] = React.useState(false);

  /** The scene's non-plotted rows in deterministic strip order. */
  const cells = React.useMemo(
    () => [...pendingCells, ...granularCells],
    [pendingCells, granularCells]
  );

  const selectedPin =
    (popoverTarget && pins.find((p) => p.markerId === popoverTarget.markerId)) ||
    null;
  const selectedCell =
    (popoverTarget &&
      !selectedPin &&
      cells.find((c) => c.markerId === popoverTarget.markerId)) ||
    null;

  // --- island lifecycle: one Leaflet map per scene -------------------
  React.useEffect(() => {
    let disposed = false;
    void (async () => {
      const L = await import("leaflet");
      if (disposed || !hostRef.current || mapRef.current) return;
      // leaflet base styles ship via globals.css @import
      const map = L.map(hostRef.current, {
        crs: L.CRS.Simple,
        minZoom: zoom[0],
        maxZoom: zoom[1],
        attributionControl: false,
        zoomControl: false, // pill controls below carry the ≥44 px targets
      });
      mapRef.current = map;
      pinLayerRef.current = L.layerGroup().addTo(map);
      setMapReady((n) => n + 1);
    })();
    return () => {
      disposed = true;
      mapRef.current?.remove();
      mapRef.current = null;
      pinLayerRef.current = null;
      imageryRef.current = null;
      setImageryReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- rebuilt per scene
  }, [sceneId]);

  // --- default view: bounds-driven fit OR deterministic mean-center ---
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (bounds) {
      const padded = padBounds(bounds, 0.08);
      map.setMaxBounds(undefined);
      map.fitBounds(
        [
          [padded[1], padded[0]],
          [padded[3], padded[2]],
        ],
        { padding: [12, 12] }
      );
      map.setMaxBounds([
        [padBounds(bounds, 0.4)[1], padBounds(bounds, 0.4)[0]],
        [padBounds(bounds, 0.4)[3], padBounds(bounds, 0.4)[2]],
      ]);
    } else {
      // mean of the plotted points — presentation math, derives no data
      const cx =
        pins.length > 0 ? pins.reduce((s, p) => s + p.x, 0) / pins.length : 0;
      const cy =
        pins.length > 0 ? pins.reduce((s, p) => s + p.y, 0) / pins.length : 0;
      map.setView([cy, cx], Math.floor((zoom[0] + zoom[1]) / 2));
      map.setMaxBounds(undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-fit per scene/bounds only
  }, [mapReady, sceneId, bounds === null ? "null" : "set"]);

  // --- authored imagery, ONLY over calibrated bounds ------------------
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !bounds) return;
    let disposed = false;
    void (async () => {
      const L = await import("leaflet");
      const img = new Image();
      img.onload = () => {
        if (disposed || !mapRef.current || imageryRef.current) return;
        imageryRef.current = L.imageOverlay(
          `/map/${encodeURIComponent(sceneId)}/base.svg`,
          [
            [bounds[1], bounds[0]],
            [bounds[3], bounds[2]],
          ]
        ).addTo(mapRef.current);
        imageryRef.current.getElement()?.setAttribute("aria-hidden", "true");
        setImageryReady(true);
      };
      // onerror keeps the grid fallback — absence is the honest state
      img.src = `/map/${encodeURIComponent(sceneId)}/base.svg`;
    })();
    return () => {
      disposed = true;
      imageryRef.current?.remove();
      imageryRef.current = null;
      setImageryReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- per scene+bounds
  }, [mapReady, sceneId, bounds]);

  // --- plotted-pin layer ---------------------------------------------
  React.useEffect(() => {
    let disposed = false;
    void (async () => {
      const L = await import("leaflet");
      const layer = pinLayerRef.current;
      if (disposed || !layer) return;
      layer.clearLayers();
      for (const pin of pins) {
        const focused = pin.markerId === focusedMarkerId;
        const joined = hoveredKind !== null && pin.kind === hoveredKind;
        const base = kindPinStyle(pin.kind, focused);
        const html = `<span role="img" aria-label="${escapeAttr(pin.title)}" class="${
          focused ? "ms-glow-pulse" : ""
        }" style="${cssProps(base)};width:16px;height:16px;border-radius:999px;display:block;${
          joined
            ? "outline:2px solid color-mix(in srgb, var(--ms-accent) 75%, transparent);outline-offset:2px;"
            : ""
        }"></span>`;
        const marker = L.marker([pin.y, pin.x], {
          icon: L.divIcon({ html, className: "", iconSize: [16, 16] }),
          keyboard: true,
          title: pin.title,
          alt: pin.title,
          zIndexOffset: focused ? 1000 : joined ? 500 : 0,
        });
        marker.on("click", () => onSelectPin(pin.markerId));
        marker.on("mouseover", () => onPinHover(pin.kind));
        marker.on("mouseout", () => onPinHover(null));
        layer.addLayer(marker);
      }
    })();
    return () => {
      disposed = true;
    };
  }, [mapReady, pins, focusedMarkerId, hoveredKind, onSelectPin, onPinHover]);

  // --- popover anchor follows its marker through pan/zoom -------------
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedPin) return;
    const sync = () => {
      const el = anchorRef.current;
      const host = hostRef.current;
      if (!el || !host) return;
      const pt = map.latLngToContainerPoint([selectedPin.y, selectedPin.x]);
      const w = host.clientWidth;
      const h = host.clientHeight;
      const x = Math.min(Math.max(pt.x, 12), Math.max(w - 12, 12));
      const y = Math.min(Math.max(pt.y, 12), Math.max(h - 12, 12));
      el.style.setProperty("--pin-x", `${x}px`);
      el.style.setProperty("--pin-y", `${y}px`);
    };
    sync();
    map.on("move", sync);
    map.on("zoom", sync);
    map.on("resize", sync);
    return () => {
      map.off("move", sync);
      map.off("zoom", sync);
      map.off("resize", sync);
    };
  }, [mapReady, selectedPin]);

  const zoomBy = (delta: number) => {
    const map = mapRef.current;
    if (!map) return;
    map.setZoom(map.getZoom() + delta);
  };
  const resetView = () => {
    const map = mapRef.current;
    if (!map) return;
    if (bounds) {
      map.fitBounds(
        [
          [bounds[1], bounds[0]],
          [bounds[3], bounds[2]],
        ],
        { padding: [12, 12] }
      );
    } else {
      const cx = pins.length > 0 ? pins.reduce((s, p) => s + p.x, 0) / pins.length : 0;
      const cy = pins.length > 0 ? pins.reduce((s, p) => s + p.y, 0) / pins.length : 0;
      map.setView([cy, cx], Math.floor((zoom[0] + zoom[1]) / 2));
    }
  };

  return (
    <div
      data-slot="scene-map"
      className={cn(
        "relative h-[420px] w-full overflow-hidden rounded-lg border border-border sm:h-[480px]",
        className
      )}
    >
      {/* schematic grid — the awaiting-artwork state; authored SVG replaces
          it once calibration lands (OQ-2 progressive ship) */}
      <div
        aria-hidden
        className="absolute inset-0 [background-image:repeating-linear-gradient(0deg,color-mix(in_srgb,var(--ms-bg-2)_38%,transparent)_0_1px,transparent_1px_32px),repeating-linear-gradient(90deg,color-mix(in_srgb,var(--ms-bg-2)_38%,transparent)_0_1px,transparent_1px_32px)]"
      />
      <div ref={hostRef} className="absolute inset-0 z-[400]" />

      {pins.length === 0 && cells.length === 0 && (
        /* zero rows of ANY disposition: the honest explicit-missing well —
           never a caption sentence (design-standard §5.1) */
        <VoidWell className="pointer-events-none absolute inset-6 z-[450] rounded-md border-dashed opacity-60" aria-label={pendingLabel} />
      )}

      {/* F-MV4: the scene's own non-plotted rows render INSIDE the panel —
          a deterministic stacked strip over the grid's start edge. Fixed
          offsets are list order, not coordinates; nothing is faked and no
          bounds/imagery gate can hide the rows again. */}
      {cells.map((c, i) => (
        <LockedCell
          key={c.markerId}
          cell={c}
          statusLabel={
            c.status === "scene-granular" ? granularLabel : pendingLabel
          }
          hovered={hoveredKind === c.kind}
          onOpen={onSelectPin}
          onHover={onPinHover}
          style={{ top: `${12 + i * 52}px`, insetInlineStart: 12 }}
        />
      ))}

      {/* pill controls — every target ≥44 px */}
      <div className="absolute end-3 top-3 z-[500] flex flex-col gap-2">
        <button
          type="button"
          onClick={() => zoomBy(1)}
          aria-label={controlLabels.zoomIn}
          className="inline-flex size-11 items-center justify-center rounded-full bg-secondary font-lcd text-lg text-secondary-foreground shadow-glow-pink hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          +
        </button>
        <button
          type="button"
          onClick={() => zoomBy(-1)}
          aria-label={controlLabels.zoomOut}
          className="inline-flex size-11 items-center justify-center rounded-full bg-secondary font-lcd text-lg text-secondary-foreground shadow-glow-pink hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          −
        </button>
        <button
          type="button"
          onClick={resetView}
          aria-label={controlLabels.resetView}
          title={controlLabels.resetView}
          className="inline-flex size-11 items-center justify-center rounded-full bg-secondary text-secondary-foreground shadow-glow-pink hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <span aria-hidden className="text-base leading-none">
            ⟲
          </span>
        </button>
      </div>

      {/* popover — plotted pins anchor to their marker through pan/zoom;
          position-less cells anchor bottom-start (a list row has no spot to
          pin to and none may be invented). ≤640 px is the side sheet. */}
      {popoverTarget && (
        <div
          ref={anchorRef}
          className="pointer-events-none absolute inset-0 z-[600] [--pin-x:50%] [--pin-y:50%]"
        >
          <PinPopover
            target={popoverTarget}
            chrome={popoverChrome}
            labels={popoverLabels}
            onClose={onClosePopover}
            className={cn(
              "pointer-events-auto absolute",
              selectedCell
                ? "bottom-3 left-3"
                : "left-[var(--pin-x)] top-[var(--pin-y)] -translate-x-1/2 -translate-y-full",
              "max-[640px]:inset-x-3 max-[640px]:bottom-3 max-[640px]:top-auto max-[640px]:w-auto max-[640px]:translate-x-0 max-[640px]:translate-y-0"
            )}
          />
        </div>
      )}
    </div>
  );
}

/** Percent padding on [xMin,yMin,xMax,yMax]; clamped to finite extents. */
function padBounds(
  b: [number, number, number, number],
  frac: number
): [number, number, number, number] {
  const dx = (b[2] - b[0]) * frac;
  const dy = (b[3] - b[1]) * frac;
  return [b[0] - dx, b[1] - dy, b[2] + dx, b[3] + dy];
}
