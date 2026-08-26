"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * CorruptionHover — VHS banding + RGB split via --ms-glow-glitch as STATE for
 * compromised/glitched entities, never decoration (T2 §4.1, §7.5).
 * Applied only where the data says the entity is compromised.
 */
export function CorruptionHover({
  className,
  children,
  active = false,
  ...props
}: React.ComponentProps<"span"> & {
  /** True marks a genuinely compromised entity (state, not styling choice). */
  active?: boolean;
}) {
  if (!active) {
    return (
      <span className={className} data-compromised="false" {...props}>
        {children}
      </span>
    );
  }
  return (
    <span
      data-slot="corruption-hover"
      data-compromised="true"
      className={cn("group/comp relative inline-block", className)}
      {...props}
    >
      {children}
      {/* VHS scanline banding overlay — appears on hover/focus only */}
      <span
        aria-hidden
        className={cn(
          "pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-150",
          "group-hover/comp:opacity-100 group-focus-within/comp:opacity-100",
          "[background-image:repeating-linear-gradient(0deg,color-mix(in_srgb,var(--ms-danger)_14%,transparent)_0px,color-mix(in_srgb,var(--ms-danger)_14%,transparent)_2px,transparent_2px,transparent_5px)]"
        )}
      />
      <span
        aria-hidden
        className={cn(
          "pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 mix-blend-screen transition-opacity duration-150",
          "group-hover/comp:opacity-100 group-focus-within/comp:opacity-100",
          "[box-shadow:var(--ms-glow-glitch)]"
        )}
      />
    </span>
  );
}
