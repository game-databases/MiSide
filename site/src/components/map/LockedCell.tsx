import * as React from "react";

import { cn } from "@/lib/utils";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { kindChipStyle } from "./kindAxis";
import type { MapCellVM } from "./viewTypes";

/*
 * Visible-locked treatment for ONE marker row that has no projecting
 * coordinates (map-viewer §5 LockedCell row; dataset-scenes §3.5
 * checkerboard-void discipline). F-MV4: the scene's own rows render INSIDE
 * the panel as a deterministic stacked strip over the schematic grid —
 * position-less by construction, so no coordinate is claimed and none is
 * faked (bounds stay null until calibration).
 *
 * One-row law: the cell IS the row — an <a href> to the entity page (the
 * crawlable graph of AC MV-4 lives in served HTML through these anchors),
 * whose plain left click opens the same PinPopover a plotted pin does
 * (provenance cell included); modified clicks follow the href. No second
 * chip stack duplicates the row below the panel.
 */
export function LockedCell({
  cell,
  statusLabel,
  hovered,
  onOpen,
  onHover,
  className,
  style,
}: {
  /** The non-plotted marker row this cell stands in for. */
  cell: MapCellVM;
  /** Localized status word (chrome map.awaitingTransform / map.sceneGranular). */
  statusLabel: string;
  /** Kind-hover join state (bidirectional highlight, design-standard §5.3). */
  hovered: boolean;
  /** Opens the PinPopover for this row. */
  onOpen: (markerId: string) => void;
  onHover: (kind: string | null) => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <a
      href={cell.pageHref ?? undefined}
      data-slot="locked-cell"
      data-marker-id={cell.markerId}
      onClick={(e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0)
          return; // modified click = navigate, as the href promises
        e.preventDefault();
        onOpen(cell.markerId);
      }}
      onMouseEnter={() => onHover(cell.kind)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(cell.kind)}
      onBlur={() => onHover(null)}
      style={{ ...kindChipStyle(cell.kind, false), ...style }}
      aria-label={`${cell.title} — ${statusLabel}`}
      title={cell.title}
      className={cn(
        "absolute z-[500] flex min-h-11 max-w-[70%] cursor-pointer items-center gap-2 rounded-full border border-dashed px-3 text-xs backdrop-blur-[2px] hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        hovered && "ring-2 ring-ring",
        className
      )}
    >
      <span
        aria-hidden
        className="inline-block size-4 shrink-0 rounded-sm border border-border [background-image:repeating-conic-gradient(color-mix(in_srgb,var(--ms-bg-1)_60%,transparent)_0%_25%,transparent_0%_50%)] [background-size:8px_8px]"
      />
      <span className="truncate font-bold">{cell.title}</span>
      <LcdTerminal className="w-auto shrink-0 rounded-full border-none bg-transparent px-1 py-0 text-[12px]">
        {statusLabel}
      </LcdTerminal>
    </a>
  );
}
