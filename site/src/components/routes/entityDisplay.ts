/*
 * Display-name layer for contract rows — deliberately JSX-free so node --test
 * lanes (and any non-DOM consumer) can import it through mapView's builders.
 * Same laws as before the split:
 *  • pointers stay truth, EN copies are glue (characters contract rule 4);
 *  • labels come from emitted fields + re-spacing ONLY — never an invented
 *    proper noun (CH-6 measured-absence; map-viewer §4 forbidden list).
 */
import {
  ENTITY_KINDS,
  personages,
} from "@/data/contracts";
import type {
  AchievementRow,
  BookRow,
  CartridgeRow,
  EndingRow,
  MinigameRow,
  PersonageRow,
  ProfileDocumentRow,
  SceneRow,
  WorldDocumentRow,
} from "@/data/contracts";
import { resolveLoc } from "@/data/resolveLoc";

/** Display name for a row in a locale — pointers stay truth, EN copies are glue. */
export function displayName(
  kind: string,
  row: Record<string, unknown>,
  localeCode: string
): string {
  switch (kind) {
    case "mita":
    case "players": {
      const r = row as unknown as PersonageRow;
      return resolveLoc(localeCode, r.name_loc);
    }
    case "cartridges": {
      // VC-2 fix #1: the label rides the PINNED cartridge joins only —
      // depicts (character) / contains (player) resolve to the registry's
      // own human labels ("Ghostly Mita", "Player 7"). A row with neither
      // anchor (`mta`, DS-4 namespace honesty) keeps its save_key honestly
      // re-spaced — never an assumed nameSave equality, never a lore name.
      const r = row as unknown as CartridgeRow;
      const joinId = r.depicts_character_id ?? r.contains_player_id;
      const person = joinId ? personageById().get(joinId) : undefined;
      const named = person ? resolveLoc(localeCode, person.name_loc) : "";
      return named || desluggedLabel(r.save_key) || r.save_key;
    }
    case "minigames": {
      const r = row as unknown as MinigameRow;
      const named = r.name_loc ? resolveLoc(localeCode, r.name_loc) : "";
      return named || desluggedLabel(r.client_key) || r.client_key;
    }
    case "achievements": {
      const r = row as unknown as AchievementRow;
      return r.display[localeCode]?.name ?? r.achievement_id;
    }
    case "endings": {
      const r = row as unknown as EndingRow;
      return r.display_name_loc
        ? resolveLoc(localeCode, r.display_name_loc)
        : desluggedLabel(r.ending_id);
    }
    case "profiles":
      return resolveLoc(localeCode, (row as unknown as ProfileDocumentRow).name_loc);
    case "books": {
      // No display-name column exists (documents contract): the client's own
      // texture basename ("Book 1") IS the label — re-spaced so "Books0"
      // reads "Books 0" instead of leaking an id.
      const r = row as unknown as BookRow & { texture_rel?: string };
      const base = r.texture_rel?.split("/").pop()?.replace(/\.(webp|png)$/i, "");
      return (base && desluggedLabel(base)) || r.book_id;
    }
    case "lore":
      // Routed world papers carry no client title anywhere; the id re-spaced
      // is the honest label ("Paperpart Level 13 0") — no invented titles.
      return desluggedLabel((row as unknown as WorldDocumentRow).document_id);
    case "locations": {
      // Human title where the client names the scene (chapter name); nameless
      // boot/menu containers keep a re-spaced id on-page (never in search).
      const r = row as unknown as SceneRow;
      return (
        (r.chapter_name_loc ? resolveLoc(localeCode, r.chapter_name_loc) : "") ||
        desluggedLabel(r.scene_id)
      );
    }
    default:
      return String(row[ENTITY_KINDS[kind].idField] ?? "");
  }
}

/*
 * Honest de-slug for ids the client never names: separators become spaces,
 * letter↔digit and camelCase boundaries split, words title-cased. It only
 * re-spaces what the corpus itself ships — it never composes a lore name
 * (rule 8). "mta" → "Mta", "Books0" → "Books 0", "level17" → "Level 17".
 */
export function desluggedLabel(raw: string): string {
  return raw
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([a-zA-Z])(\d)/g, "$1 $2")
    .replace(/(\d)([a-zA-Z])/g, "$1 $2")
    .replace(/[-_.]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** character_id → personage row (cartridge depicts/contains name joins). */
let personageIndex: Map<string, PersonageRow> | null = null;
export function personageById(): Map<string, PersonageRow> {
  if (!personageIndex) {
    personageIndex = new Map(personages().map((p) => [p.character_id, p]));
  }
  return personageIndex;
}
