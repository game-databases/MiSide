import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * LCD console → LcdTerminal (T2 §4.4): the machine-voice register. CRT green
 * --ms-signal pixel face on a near-black screen — RESERVED for machine-voice
 * data (buildIds, dump refs, console reference); never body text.
 */
export function LcdTerminal({
  className,
  children,
  ...props
}: React.ComponentProps<"output">) {
  return (
    <output
      data-slot="lcd-terminal"
      data-machine="true"
      className={cn(
        "block w-full rounded-md border border-border bg-[color-mix(in_srgb,var(--ms-bg-0)_88%,var(--ms-bg-1))] px-4 py-3 font-lcd text-base tracking-wider text-[var(--ms-signal)] shadow-glow-glitch",
        className
      )}
      {...props}
    >
      {children}
    </output>
  );
}
