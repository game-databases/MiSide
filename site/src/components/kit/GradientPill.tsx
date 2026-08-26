import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * Key-hint gradient label pill (T2 §3 key hints: `W UP / A LEFT / …`,
 * `ESC` + FINISH PLAYING; gradient sampled comm-minigame-lcd-defeat).
 */
export function GradientPill({
  className,
  children,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="gradient-pill"
      className={cn(
        "inline-flex items-center gap-2 rounded-full [background-image:var(--ms-accent-gradient)] px-4 py-1.5 text-sm font-bold uppercase tracking-wide text-primary-foreground shadow-glow-pink",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
