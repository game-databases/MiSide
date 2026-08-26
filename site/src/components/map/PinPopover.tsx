import * as React from "react";

import { cn } from "@/lib/utils";
import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { kindChipStyle } from "./kindAxis";

/*
 * PinPopover (map-viewer §5): the entity card for one marker — loc-correct
 * title, kind chip, placement-provenance cell (surfaced whenever the §7
 * carry law bites: mechanism !== "hard" OR relink status !== "modeled"),
 * machine-voice status register for non-projected rows, instance census so
 * a count is never silently 1-of-N, and the crawlable <a> to the entity
 * page (the same anchor SSR renders).
 */

export interface PopoverTarget {
  markerId: string;
  kind: string;
  title: string;
  pageHref: string | null;
  /** Placement mechanism verbatim (the carry law's first leg). */
  mechanism?: string;
  /**
   * Relink edge status verbatim — the carry law's second leg. Distinct from
   * `status` above, which is the projection disposition register.
   */
  relinkStatus?: string;
  sourceJoin?: string;
  status?: "projected" | "awaiting-transform-stage" | "scene-granular";
  instanceCensus?: Record<string, number>;
}

export function PinPopover({
  target,
  chrome,
  labels,
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
  /** Localized label maps (kind chips, census legend) keyed by raw token. */
  labels?: {
    kindLabels?: Record<string, string>;
    censusLabels?: Record<string, string>;
  };
  onClose: () => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const { kindLabels = {}, censusLabels = {} } = labels ?? {};
  // §5/§7 carry law (F-7): the cell surfaces whenever mechanism !== "hard"
  // OR the relink status !== "modeled" — a future relink edit cannot flip
  // rendering silent. Absent fields never trip it (fail-closed).
  const provenanceBites =
    (Boolean(target.mechanism) && target.mechanism !== "hard") ||
    (Boolean(target.relinkStatus) && target.relinkStatus !== "modeled");
  const statusLabel =
    target.status === "awaiting-transform-stage"
      ? chrome.awaitingTransform
      : target.status === "scene-granular"
        ? chrome.sceneGranular
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
        title={target.kind}
        className="w-fit rounded-full border px-2.5 py-1 font-lcd text-xs uppercase tracking-wide"
        style={kindChipStyle(target.kind, false)}
      >
        {kindLabels[target.kind] ?? target.kind}
      </span>

      {statusLabel && (
        <LcdTerminal title={statusLabel} className="rounded-full px-3 py-1.5 text-xs">
          {statusLabel}
        </LcdTerminal>
      )}

      {provenanceBites && (
        // §7 carry law: mechanism/relink status/source_join surfaced verbatim
        // whenever the law bites — never paraphrased, never dropped
        <dl className="flex flex-col gap-0.5 rounded-md bg-secondary/60 px-3 py-2 text-xs text-muted-foreground">
          <div className="flex items-baseline gap-2">
            <dt className="font-lcd uppercase">mechanism</dt>
            <dd className="font-lcd">{target.mechanism}</dd>
          </div>
          {target.relinkStatus && (
            <div className="flex items-baseline gap-2">
              <dt className="font-lcd uppercase">status</dt>
              <dd className="font-lcd">{target.relinkStatus}</dd>
            </div>
          )}
          {target.sourceJoin && (
            <div className="flex items-baseline gap-2">
              <dt className="font-lcd uppercase">join</dt>
              <dd className="font-lcd">{target.sourceJoin}</dd>
            </div>
          )}
        </dl>
      )}

      {target.instanceCensus && (
        // F-MV4 microcopy law: the emitter's census vocabulary (bare/suffixed/
        // total/minigames_hosted) never renders raw — each count rides its
        // chrome-keyed legend label; an unmapped key falls back to the token
        // so a count can never silently vanish.
        <div className="flex flex-wrap gap-1">
          {Object.entries(target.instanceCensus).map(([k, v]) => (
            <span
              key={k}
              title={censusLabels[k] ?? k}
              className="rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-[var(--ms-signal)]"
            >
              {censusLabels[k] ?? k}: {v}
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
