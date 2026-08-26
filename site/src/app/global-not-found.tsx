import Link from "next/link";
import "./globals.css";

/*
 * Global 404 — the multi-root layout site's uncaught-404 surface (no single
 * root layout exists above the two route groups, so this file carries its
 * own <html>). States the fact in plain words and offers the way back — no
 * 404 theorizing, no absence essay (anti-slop). The VHS banding overlay is
 * the horror register as STATE on the one truly broken surface (VC-1 fix:
 * VHS 404); CorruptionHover marks it data-honestly.
 */
export const metadata = {
  title: "MiSide Database",
};

export default function GlobalNotFound() {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <body style={{ minHeight: "100dvh" }}>
        <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-4 text-center">
          {/* machine voice, corruption state: scanline banding over the code;
              the banding drifts (VC-2 fix #6: the 404 is a live surface) */}
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
            href="/"
            className="rounded-full bg-primary px-5 py-2 text-sm font-bold uppercase tracking-wide text-primary-foreground shadow-glow-pink"
          >
            MiSide
          </Link>
        </div>
      </body>
    </html>
  );
}
