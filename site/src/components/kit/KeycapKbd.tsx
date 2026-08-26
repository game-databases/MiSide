import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * Badge / kbd → KeycapKbd (T2 §3, §7.7): bold white letter on a small magenta
 * rounded square — the site's keyboard-hint language. Radius-md family member
 * (cells+chips); no sharp corners.
 */
export function KeycapKbd({
  className,
  children,
  ...props
}: React.ComponentProps<"kbd">) {
  return (
    <kbd
      data-slot="keycap-kbd"
      className={cn(
        "inline-flex min-w-7 items-center justify-center rounded-md bg-primary px-1.5 py-1 text-xs font-bold leading-none text-primary-foreground shadow-glow-pink",
        className
      )}
      {...props}
    >
      {children}
    </kbd>
  );
}
