import Link from "next/link";

import { cn, asRoute } from "@/lib/utils";
import { NameTagPill } from "./NameTagPill";

/*
 * Card → CartridgeCard (T2 §3 menu/list, §7.4): square rounded cell +
 * header-pill panel + per-cell counts — the grid language for ANY
 * grid-of-entities page. Cell radius = radius-md (cells+chips); header pill
 * carries the uppercase section-header register (white-on-pink, soft lift).
 */
export function CartridgeCard({
  href,
  title,
  header,
  count,
  img,
  imgAlt,
  accent,
  corrupted = false,
  className,
  children,
}: {
  href: string;
  title: string;
  /** Optional uppercase header-pill label above the cell. */
  header?: string;
  /** Per-cell count chip (the menu's counts grid). */
  count?: React.ReactNode;
  /** Client art filling the cell when the corpus holds one (art.ts selection). */
  img?: string;
  imgAlt?: string;
  /** Mita-keyed local accent (tier-3 token), when the entity owns one. */
  accent?: string;
  /** Compromised/glitched entities take corruption as STATE on hover. */
  corrupted?: boolean;
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)} data-corrupted={corrupted || undefined}>
      {header && <NameTagPill className="self-start text-xs">{header}</NameTagPill>}
      <Link
        href={asRoute(href)}
        data-slot="cartridge-card"
        data-character={accent ? true : undefined}
        style={accent ? ({ "--ms-accent-local": accent } as React.CSSProperties) : undefined}
        className={cn(
          "group relative flex aspect-square flex-col items-stretch justify-end overflow-hidden rounded-md",
          "border border-border bg-card shadow-glow-pink outline-none duration-200",
          "transition-[transform,box-shadow,text-shadow]",
          // VC-3 fix #5: an explicit transform, not `-translate-y-0.5` —
          // Tailwind v4 translate utilities ride the separate `translate`
          // property, so computed transform stayed `none` and the lift was
          // dead code (and outside this element's transition list). The
          // hover transform is what the card actually animates.
          "focus-visible:ring-2 focus-visible:ring-ring hover:[transform:translateY(-0.125rem)]",
          !img &&
            "[background-image:repeating-conic-gradient(color-mix(in_srgb,var(--ms-bg-1)_55%,transparent)_0%_25%,transparent_0%_50%)] [background-size:24px_24px]",
          // VC-2 fix #2: corruption answers a REAL pointer. These are `hover:`
          // on the link itself — the old `group-hover:` variants sat on the
          // very element carrying `group`, and a descendant selector never
          // matches its own ancestor, so the state could not fire (VC-2 §4).
          corrupted &&
            "hover:shadow-glow-glitch hover:[text-shadow:1px_0_var(--ms-glitch-split-a),-1px_0_var(--ms-glitch-split-b)]"
        )}
      >
        {/* colour-is-identity: the cell re-keys to its own soul, never shared grey */}
        {accent && (
          <span
            aria-hidden
            className="absolute inset-x-0 top-0 z-10 h-1.5 rounded-full"
            style={{ background: "var(--ms-accent-local)" }}
          />
        )}
        {/* art-first cell: client art fills, label sits on a legible scrim */}
        {img !== undefined && (
          // eslint-disable-next-line @next/next/no-img-element -- static public asset
          <img
            src={img}
            alt={imgAlt ?? ""}
            width={512}
            height={512}
            loading="lazy"
            aria-hidden={imgAlt === undefined || imgAlt === "" ? true : undefined}
            className="absolute inset-0 size-full object-contain p-3 transition-transform duration-200 group-hover:scale-[1.03]"
          />
        )}
        <div className="relative mt-auto bg-[color-mix(in_srgb,var(--ms-bg-0)_72%,transparent)] px-3 py-2">
          {count !== undefined && (
            <span className="mb-1 inline-flex items-center rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-[var(--ms-signal)]">
              {count}
            </span>
          )}
          <span className="line-clamp-2 block text-sm font-bold text-foreground group-hover:underline group-hover:underline-offset-4">
            {title}
          </span>
          {children}
        </div>
      </Link>
    </div>
  );
}
