import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * Checkerboard-void VoidWell (T2 §4.5): honest empties rendered as the same
 * height as filled slots — no absence sentences (design-standard §5.1;
 * DR-2026-08-22-copy-earns-its-place). Desaturated purple tiles, never grey.
 */
export function VoidWell({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="void-well"
      role="presentation"
      className={cn(
        "min-h-24 w-full rounded-md border border-border",
        "[background-image:repeating-conic-gradient(color-mix(in_srgb,var(--ms-bg-1)_55%,transparent)_0%_25%,transparent_0%_50%)]",
        "[background-size:24px_24px]",
        className
      )}
      {...props}
    />
  );
}
