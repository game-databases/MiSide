import Link from "next/link";

import { asRoute } from "@/lib/utils";

/*
 * 404 view shared by both route groups' not-found boundaries: states the
 * fact in plain words and offers the way back — no 404 theorizing, no
 * absence essay (anti-slop). The corruption state on the code is the horror
 * register on the one genuinely broken surface (VC-1: VHS 404).
 */
export function NotFoundView({ homeHref }: { homeHref: string }) {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-4 text-center">
      {/* machine voice + corruption split — the broken surface's own state;
          the VHS banding drifts (VC-2 fix #6: motion as STATE, anims > 0) */}
      <p
        data-compromised="true"
        className="relative font-lcd text-6xl tracking-widest text-[var(--ms-signal)] [text-shadow:1px_0_var(--ms-glitch-split-a),-1px_0_var(--ms-glitch-split-b)]"
      >
        404
        <span
          aria-hidden
          className="ms-vhs-drift pointer-events-none absolute inset-0 [background-image:repeating-linear-gradient(0deg,color-mix(in_srgb,var(--ms-danger)_14%,transparent)_0px,color-mix(in_srgb,var(--ms-danger)_14%,transparent)_2px,transparent_2px,transparent_5px)]"
        />
      </p>
      <Link
        href={asRoute(homeHref)}
        className="rounded-full bg-primary px-5 py-2 text-sm font-bold uppercase tracking-wide text-primary-foreground shadow-glow-pink"
      >
        MiSide
      </Link>
    </div>
  );
}
