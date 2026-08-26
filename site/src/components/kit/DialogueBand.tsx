"use client";

import * as React from "react";
import { Dialog as DialogPrimitive } from "radix-ui";

import { cn } from "@/lib/utils";
import { NameTagPill } from "./NameTagPill";
import { KeycapKbd } from "./KeycapKbd";

/*
 * Dialog / Sheet → DialogueBand (kit contract §4.1).
 * Focus trap, Escape, portal: STOCK Radix behaviour.
 * Rebuilt skin per T2 §3 dialogue box: full-width BOTTOM band, translucent
 * pink ALPHA fill — color-mix over transparent so it reads pink over light
 * and plum-purple over dark; alpha, never a solid — fully-rounded top corners;
 * name-tag pill overlapping the band's top-start; advance prompt as a keycap+
 * pill pair in the band's footer, end-aligned.
 */
function DialogueBand({
  className,
  children,
  speaker,
  advanceKey = "SPACE",
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  /** Speaker name rendered in the overlapping tag pill. */
  speaker?: React.ReactNode;
  /** Advance prompt label (the game's own SPACE pill language). */
  advanceKey?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/55 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      <DialogPrimitive.Content
        data-slot="dialogue-band"
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 mx-auto w-full max-w-5xl outline-none",
          "rounded-t-lg bg-card/0 p-0 duration-200",
          "data-[state=open]:animate-in data-[state=open]:slide-in-from-bottom-8 data-[state=closed]:animate-out data-[state=closed]:slide-out-to-bottom-8",
          className
        )}
        {...props}
      >
        <div className="relative mx-3 mb-3">
          {/* translucent pink ALPHA fill over a fully-rounded band; the
              advance prompt rides the band's own FOOTER, end-aligned — the
              game's dialogue-box layout (VC-2 fix #6), not an overlap chip */}
          <div className="rounded-lg border border-border bg-[color-mix(in_srgb,var(--ms-accent)_34%,transparent)] px-6 pb-4 pt-9 shadow-glow-pink backdrop-blur-sm">
            {children}
            <div className="mt-3 flex items-center justify-end">
              <span className="flex items-center gap-2 rounded-full [background-image:var(--ms-accent-gradient)] px-3 py-1 shadow-glow-pink">
                <KeycapKbd>{advanceKey}</KeycapKbd>
              </span>
            </div>
          </div>
          {/* name-tag pill overlapping the band's top-start */}
          {speaker !== undefined && (
            <div className="absolute -top-4 start-5">
              <NameTagPill>{speaker}</NameTagPill>
            </div>
          )}
        </div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

const DialogueBandRoot = DialogPrimitive.Root;
const DialogueBandTrigger = DialogPrimitive.Trigger;
const DialogueBandTitle = DialogPrimitive.Title;
const DialogueBandDescription = DialogPrimitive.Description;
const DialogueBandClose = DialogPrimitive.Close;

export {
  DialogueBand,
  DialogueBandRoot,
  DialogueBandTrigger,
  DialogueBandTitle,
  DialogueBandDescription,
  DialogueBandClose,
};
