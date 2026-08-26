import * as React from "react";

import { cn } from "@/lib/utils";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { kindChipStyle } from "./kindAxis";

/*
 * PinPopover (map-viewer §5): the entity card for one marker — loc-correct
 * title, kind chip, placement-provenance cell (surfaced whenever the carry
 * law bites: mechanism !== "hard"), machine-voice status register for
 * non-projected rows, instance census so a count is never silently 1-of-N,
 * and the crawlable <a> to the entity page (the same anchor SSR renders).
 */

export interface PopoverTarget {
  markerId: string;
  kind: string;
  title: string;
  pageHref: string | null;
  mechanism?: string;
  sourceJoin?: string;
  status?: "projected" | "awaiting-transform-stage" | "scene-granular";
  instanceCensus?: Record<string, number>;
}

export function PinPopover({
  target,
  chrome,
  onClose,
  className,
  style,
}: {
  target: PopoverTarget;
  chrome: {
    awaitingTransform: string;
    sceneGranular: string;
    openPage: string;
    close: string;
  };
  onClose: () => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const provenanceBites =
    Boolean(target.mechanism) && target.mechanism !== "hard";
  const statusToken =
    target.status === "awaiting-transform-stage"
      ? "awaiting-transform-stage"
      : target.status === "scene-granular"
        ? "scene-granular"
        : null;

  return (
    <div
      role="dialog"
      aria-label={target.title}
      data-slot="pin-popover"
      style={style}
      className={cn(
        "z-[600] flex w-72 flex-col gap-2 rounded-lg border border-border bg-card p-4 shadow-glow-pink",
        className
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-bold leading-snug">{target.title}</h3>
        <button
          type="button"
          onClick={onClose}
          aria-label={chrome.close}
          className="-me-1 -mt-1 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <span aria-hidden className="text-lg leading-none">
            ×
          </span>
        </button>
      </div>

      <span
        className="w-fit rounded-full border px-2.5 py-1 font-lcd text-xs uppercase tracking-wide"
        style={kindChipStyle(target.kind, false)}
      >
        {target.kind}
      </span>

      {statusToken && (
        <LcdTerminal
          title={
            target.status === "scene-granular"
              ? chrome.sceneGranular
              : chrome.awaitingTransform
          }
          className="rounded-full px-3 py-1.5 text-xs"
        >
          {statusToken}
        </LcdTerminal>
      )}

      {provenanceBites && (
        // §7 carry law: mechanism/source_join surfaced verbatim whenever the
        // edge is not hard — a future relink edit cannot flip rendering silent
        <dl className="flex flex-col gap-0.5 rounded-md bg-secondary/60 px-3 py-2 text-xs text-muted-foreground">
          <div className="flex items-baseline gap-2">
            <dt className="font-lcd uppercase">mechanism</dt>
            <dd className="font-lcd">{target.mechanism}</dd>
          </div>
          {target.sourceJoin && (
            <div className="flex items-baseline gap-2">
              <dt className="font-lcd uppercase">join</dt>
              <dd className="font-lcd">{target.sourceJoin}</dd>
            </div>
          )}
        </dl>
      )}

      {target.instanceCensus && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(target.instanceCensus).map(([k, v]) => (
            <span
              key={k}
              className="rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-[var(--ms-signal)]"
            >
              {k}:{v}
            </span>
          ))}
        </div>
      )}

      {target.pageHref && (
        <a
          href={target.pageHref}
          className="mt-1 inline-flex h-11 items-center justify-center rounded-full [background-image:var(--ms-accent-gradient)] px-4 text-xs font-bold uppercase tracking-wide text-primary-foreground shadow-glow-pink hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {chrome.openPage}
        </a>
      )}
    </div>
  );
}
