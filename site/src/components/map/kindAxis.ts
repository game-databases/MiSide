/*
 * Kind-chip color axes (map-viewer §9 / A-MV1 OQ-10): hues derive via
 * color-mix tints from FOUR existing tier-1 rows over the --ms-bg-* stack —
 * `--ms-accent`, `--ms-signal`, `--ms-warm`, `--ms-danger`. ZERO raw hex may
 * appear under src/components (AC-S8 defect class); if a future axis lacks a
 * source row, the row lands in tokens.css FIRST.
 *
 * Hot pink `--ms-accent` stays reserved for identity + actions (focused pin,
 * active filter, primary popover link) — it is deliberately NOT a per-kind
 * hue. Kinds outside the table render monochrome (text-2 on bg-2).
 */

export type KindAxis = "signal" | "warm" | "danger" | "neutral";

import type { CSSProperties } from "react";

/** Deterministic kind → axis table; unlisted kinds stay neutral. */
const KIND_AXIS: Record<string, KindAxis> = {
  cartridge: "warm",
  profile_document: "warm",
  safe: "warm",
  travel_gate: "signal",
  minigame_access: "signal",
  monster: "danger",
};

export function kindAxis(kind: string): KindAxis {
  return KIND_AXIS[kind] ?? "neutral";
}

/**
 * Chip/pin surface style for an axis — tint + readable ink, all through CSS
 * custom properties so the tier-1 rows remain the only color sources.
 */
export function kindChipStyle(kind: string, active: boolean): CSSProperties {
  const axis = kindAxis(kind);
  const source =
    axis === "warm"
      ? "var(--ms-warm)"
      : axis === "signal"
        ? "var(--ms-signal)"
        : axis === "danger"
          ? "var(--ms-danger)"
          : undefined;
  if (!source) {
    // neutral: raised plum surface, muted ink
    return {
      backgroundColor: active
        ? "color-mix(in srgb, var(--ms-bg-2) 78%, white 6%)"
        : "color-mix(in srgb, var(--ms-bg-2) 72%, transparent)",
      color: "var(--ms-text-1)",
      borderColor: active ? "var(--ms-ring)" : undefined,
    };
  }
  return {
    // 16% tint of the axis row over the raised layer; full row as the ink
    backgroundColor: `color-mix(in srgb, ${source} ${active ? "26%" : "14%"}, var(--ms-bg-2))`,
    color: source,
    borderColor: active
      ? `color-mix(in srgb, ${source} 55%, transparent)`
      : `color-mix(in srgb, ${source} 28%, transparent)`,
  };
}

/** Pin dot fill for a plotted marker (same axes, denser mix). */
export function kindPinStyle(kind: string, focused: boolean): CSSProperties {
  const axis = kindAxis(kind);
  const source =
    axis === "warm"
      ? "var(--ms-warm)"
      : axis === "signal"
        ? "var(--ms-signal)"
        : axis === "danger"
          ? "var(--ms-danger)"
          : undefined;
  if (!source) {
    return {
      backgroundColor: focused ? "var(--ms-accent)" : "var(--ms-text-2)",
      boxShadow: "0 0 0 2px color-mix(in srgb, var(--ms-bg-0) 80%, transparent)",
    };
  }
  return {
    backgroundColor: source,
    boxShadow: `0 0 0 2px color-mix(in srgb, var(--ms-bg-0) 80%, transparent)${
      focused ? `, 0 0 10px color-mix(in srgb, ${source} 60%, transparent)` : ""
    }`,
  };
}
