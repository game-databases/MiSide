/*
 * Palette float→hex conversion pinned in contracts/dataset-characters.mdx:
 * "#RRGGBB = per-channel round(f×255) clamped to [0,255] from the stored
 * floats". Verified anchors: mita-usual c1 → cc73a2, mita-true c1 → d92c45.
 * RGBA floats serialize r,g,b,a order.
 */
export function paletteFloatsToHex(rgba: number[]): string {
  const [r = 0, g = 0, b = 0] = rgba;
  const ch = (f: number) =>
    Math.min(255, Math.max(0, Math.round(f * 255)))
      .toString(16)
      .padStart(2, "0");
  return `#${ch(r)}${ch(g)}${ch(b)}`;
}
