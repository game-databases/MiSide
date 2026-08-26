import Link from "next/link";

import { ProvenanceChip } from "@/components/entity/ProvenanceChip";
import type { RelationCardVM } from "@/lib/relations/relationCards";
import { asRoute } from "@/lib/utils";

/*
 * Relation cards — the registry-driven relation module (board item B-RP1).
 * One card per registered join family that anchors this entity; items are
 * direction-aware (→ page-as-source, ← page-as-target, ↔ mirrored), carry
 * the shared provenance chip, and degrade fail-closed:
 *   • state "linked"     → real crawlable <a href> to the peer's page;
 *   • state "text"       → machine-plane anchor echoed verbatim (LCD token);
 *   • state "unresolved" → explicit unresolved token, never a guessed link;
 *   • counted rows (×N)  → dense machine-token families stay visible as counts;
 *   • missing_fields     → named explicit-missing lines, verbatim (§7).
 * Family headers speak the machine register (stem + measured census +
 * registry binds sentence) — no authored copy, nothing to localize.
 */
export function RelationCards({ cards }: { cards: RelationCardVM[] }) {
  return (
    <div data-slot="relation-cards" className="flex flex-col gap-4">
      {cards.map((card) => (
        <section
          key={card.family}
          data-slot="relation-card"
          className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4"
        >
          <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="font-lcd text-sm uppercase tracking-wide">
              {card.family}
            </span>
            <span className="font-lcd text-xs text-muted-foreground">
              edges:{card.edgeCount}
            </span>
            <span className="text-xs leading-snug text-muted-foreground">
              {card.binds}
            </span>
          </header>
          <ul className="flex flex-col gap-1.5">
            {card.items.map((item) => {
              const body = (
                <>
                  <span
                    aria-hidden
                    className="font-lcd text-xs text-muted-foreground"
                  >
                    {item.arrow}
                  </span>
                  <span
                    className={
                      item.state === "linked"
                        ? "truncate"
                        : "truncate font-mono text-xs text-muted-foreground"
                    }
                  >
                    {item.label}
                  </span>
                  {typeof item.count === "number" && (
                    <span className="font-lcd text-xs text-[var(--ms-signal)]">
                      ×{item.count}
                    </span>
                  )}
                  {item.extras.map((extra) => (
                    <span
                      key={extra}
                      className="rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-secondary-foreground"
                    >
                      {extra}
                    </span>
                  ))}
                  <ProvenanceChip
                    mechanism={item.mechanism}
                    status={item.status}
                  />
                </>
              );
              return (
                <li key={item.key}>
                  {item.href ? (
                    <Link
                      href={asRoute(item.href)}
                      className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 rounded-full px-3 py-1.5 text-sm font-bold hover:bg-accent"
                    >
                      {body}
                    </Link>
                  ) : (
                    <span className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 rounded-full px-3 py-1.5">
                      {body}
                    </span>
                  )}
                  {item.missingFields.length > 0 && (
                    <ul className="mt-0.5 flex flex-col gap-0.5 pl-6">
                      {item.missingFields.map((m) => (
                        <li
                          key={m}
                          className="font-lcd text-xs text-[var(--ms-signal)]"
                        >
                          missing: {m}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
