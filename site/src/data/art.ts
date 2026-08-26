/*
 * Selected client art under public/img/ (emitted by scripts/select-art.py
 * from the extracted art export — every path traces to a named exported
 * object; see that script's table). A character WITHOUT a row here owns no
 * confident portrait in the corpus: pages render their named empty well,
 * never a substitute image (design-standard §5.1).
 */

import BOOKS_MANIFEST from "./books-art.json";

/** character_id → portrait webp. Absence = no confident client portrait. */
export const MITA_PORTRAIT: Record<string, string> = {
  "mita-usual": "/img/mita/mita-usual.webp",
  "mita-short-hairs": "/img/mita/mita-short-hairs.webp",
  "mita-kind": "/img/mita/mita-kind.webp",
  "mita-cap": "/img/mita/mita-cap.webp",
  "mita-little": "/img/mita/mita-little.webp",
  "mita-dreamer": "/img/mita/mita-dreamer.webp",
  mila: "/img/mita/mila.webp",
  "mita-creepy": "/img/mita/mita-creepy.webp",
  "mita-chibi": "/img/mita/mita-chibi.webp",
  "mita-black": "/img/mita/mita-black.webp",
  "mita-maneken": "/img/mita/mita-maneken.webp",
};

/**
 * Achievement icon by registry_index (level2 menu atlas, content-matched per
 * index in select-art.py). The game's own placeholder covers null/unknown.
 */
export function achievementIcon(registryIndex: number | null): string {
  return `/img/ach/${registryIndex ?? "none"}.webp`;
}

/** Menu UI objects reused as section identity art. */
export const UI_ART = {
  cartridge: "/img/ui/cartridge.webp",
  tamagotchi: "/img/ui/tamagotchi.webp",
  book: "/img/ui/book.webp",
  player: "/img/ui/player.webp",
  locations: "/img/ui/locations.webp",
} as const;

/**
 * Section-header identity art per routed kind (VC-2 fix #3) — corpus objects
 * only, name-for-name confident. A section the corpus gives no confident
 * object for renders no header art (endings/mita/achievements/books carry
 * per-card art instead via indexArtFor).
 */
export const KIND_SECTION_ART: Record<string, string> = {
  cartridges: UI_ART.cartridge,
  players: UI_ART.player,
  minigames: UI_ART.tamagotchi,
  locations: UI_ART.locations,
};

/**
 * Per-minigame card art (VC-3 fix #3) — emitted by scripts/select-art.py
 * from the extracted art export. Every row is a CONFIDENT name-for-name
 * match between the texture object and the minigame's own client identity,
 * with the texture's non-shared container spread covering that game's pinned
 * carrier/loader container (dataset-cartridges §4.2 carrier_containers):
 * e.g. "Shooter.png" exists only in level23 + its sharedassets — exactly the
 * shooter scene; "TetrisGame 1" spreads over precisely the tetris carriers.
 * Two rows deliberately stay absent: `menu-mita-dance` and
 * `tamagotchi-find-furniture` have no named 2D object in the corpus (their
 * surfaces are 3D-only), so those cards keep the honest empty well.
 */
export const MINIGAME_ART: Record<string, string> = {
  carspace: "/img/minigames/carspace.webp", // ScreenSpaceCar.png (loader level9)
  makemaneken: "/img/minigames/makemaneken.webp", // ScreenMakeManeken.png (loader level12)
  "minigame-shooter": "/img/minigames/minigame-shooter.webp", // Shooter.png (level23)
  fight: "/img/minigames/fight.webp", // Background Fight.png (TV, level6)
  pinguin: "/img/minigames/pinguin.webp", // Background Pinguins.png (TV, level6)
  "location-4-table-card-game": "/img/minigames/location-4-table-card-game.webp", // Cards.png (level6)
  "location-7-game-dance": "/img/minigames/location-7-game-dance.webp", // LineDance.png (level9)
  "location-7-hammer-button": "/img/minigames/location-7-hammer-button.webp", // ButtonHammer.png (level9)
  "location-14-pc-snaker": "/img/minigames/location-14-pc-snaker.webp", // Snaker.png (level16)
  "location-17-pumpkin-clicker": "/img/minigames/location-17-pumpkin-clicker.webp", // Pumpkin.png (level19)
  "games-core": "/img/minigames/games-core.webp", // Interface Screen Core.png (core terminal level15/17)
  tetris: "/img/minigames/tetris.webp", // TetrisGame 1.png (spread == the tetris carriers)
  "tamagotchi-cooking": "/img/minigames/tamagotchi-cooking.webp", // CookingTable.png (phone, level3)
  "tamagotchi-help-trash": "/img/minigames/tamagotchi-help-trash.webp", // TrashBox.png (phone, level3)
  "tamagotchi-sorting": "/img/minigames/tamagotchi-sorting.webp", // RoomSorting.png (phone, level3)
};

/**
 * Readable-book cover for THIS page's locale (books-art.json is emitted by
 * select-art.py keyed by client dir name — the ledger's key space). The
 * in-game book texture carries that locale's own rendered pages, so the
 * cover is locale content, not a shared asset; a locale without a cover
 * gets no image (empty well, never another locale's art).
 */
export function bookArt(dirName: string, bookId: string): string | undefined {
  const have = (BOOKS_MANIFEST as Record<string, string[]>)[dirName];
  return have && have.includes(bookId)
    ? `/img/books/${encodeURIComponent(dirName)}/${bookId}.webp`
    : undefined;
}
