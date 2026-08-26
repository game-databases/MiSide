import * as React from "react";

import { cn } from "@/lib/utils";
import { LcdTerminal } from "@/components/kit/LcdTerminal";

/*
 * Visible-locked treatment for markers that have no projecting coordinates
 * (map-viewer §5 LockedCell row; dataset-scenes §3.5 checkerboard-void
 * discipline). Rendered ONCE imagery + bounds exist, as a fixed strip over
 * the authored schematic's start-edge — never at a faked spot, never as a
 * caption sentence. The machine voice carries the count; `label` is the
 * localized accessible name.
 */
export function LockedCell({
  count,
  label,
  className,
}: {
  count: number;
  /** Localized accessible label (chrome map.awaitingTransform / sceneGranular). */
  label: string;
  className?: string;
}) {
  return (
    <div
      data-slot="locked-cell"
      className={cn(
        "pointer-events-auto absolute start-3 top-3 z-[500] max-w-[70%]",
        className
      )}
    >
      <LcdTerminal
        aria-label={`${label}: ${count}`}
        title={label}
        className="flex items-center gap-2 rounded-full border-dashed px-3 py-1.5 text-sm"
      >
        <span
          aria-hidden
          className="inline-block size-4 shrink-0 rounded-sm border border-border [background-image:repeating-conic-gradient(color-mix(in_srgb,var(--ms-bg-1)_60%,transparent)_0%_25%,transparent_0%_50%)] [background-size:8px_8px]"
        />
        <span>{count}</span>
      </LcdTerminal>
    </div>
  );
}
