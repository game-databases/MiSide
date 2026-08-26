"use client";

import * as React from "react";

import {
  DialogueBand,
  DialogueBandRoot,
  DialogueBandTrigger,
  DialogueBandTitle,
  DialogueBandDescription,
} from "./DialogueBand";
import { PillButton } from "./PillButton";

/*
 * Routes the game's iconic pattern onto real transcript data (VC-1 horror
 * register): a line opens in the bottom dialogue band — name-tag pill
 * overlapping the top-start, SPACE keycap prompt at the top-end, the line's
 * own locale text inside. Stock Radix behaviour underneath; skin is the
 * game's dialogue box.
 */
export function DialogueBandLine({
  speaker,
  text,
  openLabel,
}: {
  speaker: string;
  /** The node's own resolved line for THIS locale. */
  text: string;
  openLabel: string;
}) {
  return (
    <DialogueBandRoot>
      <DialogueBandTrigger asChild>
        <PillButton
          tone="ghost"
          className="max-w-full font-sans normal-case tracking-normal"
        >
          <span className="truncate">{openLabel}</span>
        </PillButton>
      </DialogueBandTrigger>
      <DialogueBand speaker={speaker}>
        <DialogueBandTitle className="sr-only">{speaker}</DialogueBandTitle>
        <DialogueBandDescription className="text-base font-bold leading-relaxed text-foreground">
          {text}
        </DialogueBandDescription>
      </DialogueBand>
    </DialogueBandRoot>
  );
}
