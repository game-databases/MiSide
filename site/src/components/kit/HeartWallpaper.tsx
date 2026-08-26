import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * Heart-wallpaper texture (T2 §7.6): the repeating hearts-and-household-icons
 * wallpaper as a LOW-CONTRAST section background — cozy register in one move.
 * Inline SVG pattern, token-tinted; no binary asset, no uncited color.
 */
export function HeartWallpaper({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="heart-wallpaper"
      className={cn("relative overflow-hidden rounded-lg", className)}
      {...props}
    >
      <svg aria-hidden className="pointer-events-none absolute inset-0 size-full" role="presentation">
        <defs>
          <pattern
            id="ms-heart-wallpaper"
            width="72"
            height="72"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M12 20 C12 12 2 10 2 16 C2 21 8 24 12 27 C16 24 22 21 22 16 C22 10 12 12 12 20 Z"
              fill="color-mix(in srgb, var(--ms-accent-soft) 14%, transparent)"
            />
            <rect
              x="44"
              y="40"
              width="18"
              height="14"
              rx="3"
              fill="color-mix(in srgb, var(--ms-accent-soft) 10%, transparent)"
            />
            <path d="M42 42 L53 32 L64 42 Z" fill="color-mix(in srgb, var(--ms-accent-soft) 10%, transparent)" />
            <circle cx="50" cy="12" r="5" fill="color-mix(in srgb, var(--ms-warm) 9%, transparent)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#ms-heart-wallpaper)" />
      </svg>
      <div className="relative">{children}</div>
    </div>
  );
}
