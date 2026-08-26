import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * Name-tag pill overlapping its band's top-start corner (T2 §3 dialogue box:
 * `Mita`/`Мита` — locale-stable chrome). Pure hot pink --ms-accent.
 */
export function NameTagPill({
  className,
  children,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="name-tag-pill"
      className={cn(
        "inline-flex items-center rounded-full bg-primary px-4 py-1 text-sm font-bold text-primary-foreground shadow-glow-pink",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
