import { LcdTerminal } from "@/components/kit/LcdTerminal";
import { provenanceBites } from "@/lib/relations/relationCards";
import { cn } from "@/lib/utils";

/*
 * The carry-law provenance chip (map-viewer §7 F-7), shared by every
 * consumer — PinPopover's cell aside, the location module, the relation
 * cards. ONE surfacing condition and ONE echo format (both owned by
 * lib/relations/relationCards.provenanceBites so tests pin them without
 * executing JSX): surface whenever mechanism !== "hard" OR status !==
 * "modeled"; echo the values verbatim, joined " · ", LCD machine register.
 * A hard/modeled pair stays silent (no chip), never a green tick.
 */
export function ProvenanceChip({
  mechanism,
  status,
  className,
}: {
  mechanism?: string | null;
  status?: string | null;
  className?: string;
}) {
  if (!provenanceBites(mechanism, status)) return null;
  return (
    <LcdTerminal
      className={cn("w-fit rounded-full px-2.5 py-0.5 text-xs", className)}
    >
      {[mechanism, status].filter(Boolean).join(" · ")}
    </LcdTerminal>
  );
}
