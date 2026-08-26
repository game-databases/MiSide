/*
 * Server-side view builders shared by the (pivot) and [locale] route trees —
 * the single place where contract rows become display data, so no route
 * logic exists twice (spec §2 rules). Slugs come ONLY from contract id
 * columns; unknown slugs 404 (AC S6).
 */
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { ENTITY_KINDS, kindRows, findRow, personages } from "@/data/contracts";
import type {
  AchievementRow,
  EndingRow,
  MinigameRow,
  PersonageRow,
  CartridgeRow,
  ProfileDocumentRow,
  SceneRow,
  BookRow,
  WorldDocumentRow,
} from "@/data/contracts";
import { MITA_PORTRAIT, MINIGAME_ART, achievementIcon, bookArt } from "@/data/art";
import { availableLocalesFor } from "@/data/availability";
import { resolveLoc } from "@/data/resolveLoc";
import { paletteFloatsToHex } from "@/lib/palette";
import { KIND_SEGMENT, entityHref } from "@/lib/routes";
import { buildAlternates } from "@/lib/hreflang";
import { getLocale } from "@/i18n/locales";

export interface EntityIndexData {
  kind: string;
  segment: string;
  title: string;
  cards: Array<{
    id: string;
    href: string;
    title: string;
    /** Per-entity client art when the corpus holds one (art.ts selection). */
    img?: string;
    count?: React.ReactNode;
    accent?: string;
    corrupted?: boolean;
  }>;
}

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

/** Accent hex for Mita rows only (palette floats → pinned round(f×255)). */
export function accentFor(kind: string, row: Record<string, unknown>): string | undefined {
  if (kind !== "mita") return undefined;
  const r = row as unknown as PersonageRow;
  if (!Array.isArray(r.palette_color1)) return undefined;
  return paletteFloatsToHex(r.palette_color1);
}

export function softAccentFor(kind: string, row: Record<string, unknown>): string | undefined {
  if (kind !== "mita") return undefined;
  const r = row as unknown as PersonageRow;
  if (!Array.isArray(r.palette_color2)) return undefined;
  return paletteFloatsToHex(r.palette_color2);
}

/**
 * Per-entity card art — only where the corpus holds a CONFIDENT image
 * (art.ts selection table): Mita portraits, achievement icons, per-locale
 * book covers, per-minigame screens (VC-3 fix #3). VC-2 fix #3 adds two
 * PINNED-JOIN cases: a cartridge rides its depicted character's portrait; an
 * ending rides its joined achievement's own icon. A row without the join
 * gets no image — the checkerboard well stays the honest empty state.
 * `localeCode` matters only for books (the cover is that locale's own
 * texture).
 *
 * Deliberately NO branch for `players` or `locations` (VC-3 fix #3 audit,
 * against the full art export): no per-player client object exists — the
 * personage contract leaves every player resource_path empty and the
 * ChibiPlayer 1–7 textures carry no pinned tie to any personage id, so a
 * mapping would be an invented join (AGENTS.md rule 8); and scene containers
 * share one boilerplate texture set (41-dir spreads), so no name-for-name
 * per-location object exists before the scene-graph stage lands. Those two
 * grids keep their designed wells until the corpus pins identities.
 */
export function indexArtFor(
  kind: string,
  row: Record<string, unknown>,
  localeCode?: string
): string | undefined {
  switch (kind) {
    case "mita": {
      const id = String(row[ENTITY_KINDS.mita.idField]);
      return MITA_PORTRAIT[id];
    }
    case "achievements":
      return achievementIcon((row as unknown as AchievementRow).registry_index ?? null);
    case "cartridges": {
      const dep = (row as unknown as CartridgeRow).depicts_character_id;
      return dep ? MITA_PORTRAIT[dep] : undefined;
    }
    case "minigames":
      // VC-3 fix #3: the game's own screen/board art where the corpus holds
      // one (MINIGAME_ART, select-art.py emission); no row → the honest
      // empty well, never a substitute image.
      return MINIGAME_ART[String(row[ENTITY_KINDS.minigames.idField])];
    case "endings": {
      // ending→achievement is a pinned contract column (endings dataset):
      // the icon is that achievement's own atlas sprite, never a substitute.
      const aid = (row as unknown as EndingRow).achievement_id;
      if (!aid) return undefined;
      const a = findRow("achievements", aid) as unknown as AchievementRow | undefined;
      return a ? achievementIcon(a.registry_index) : undefined;
    }
    case "books": {
      const def = localeCode ? getLocale(localeCode) : undefined;
      if (!def) return undefined;
      return bookArt(def.dirName, String(row[ENTITY_KINDS.books.idField]));
    }
    default:
      return undefined;
  }
}

export function buildIndexData(
  kind: string,
  localeCode: string,
  title: string
): EntityIndexData {
  const def = ENTITY_KINDS[kind];
  if (!def || !KIND_SEGMENT[kind]) notFound();
  const locales = availableLocalesFor(kind);
  if (!locales.includes(localeCode)) notFound();
  const prefix = getLocale(localeCode)?.prefix ?? "";
  const rows = kindRows(kind) as Array<Record<string, unknown>>;
  return {
    kind,
    segment: KIND_SEGMENT[kind],
    title,
    cards: rows.map((row) => {
      const id = String(row[def.idField]);
      return {
        id,
        href: entityHref(prefix, kind, id),
        title: displayName(kind, row, localeCode),
        img: indexArtFor(kind, row, localeCode),
        accent: accentFor(kind, row),
        // the game's own broken surfaces carry corruption as STATE:
        // present-but-unreachable minigame stubs and the mode-stub ending
        corrupted:
          (kind === "minigames" &&
            Boolean((row as unknown as MinigameRow).present_but_unreachable)) ||
          (kind === "endings" &&
            (row as unknown as EndingRow).kind === "mode-stub"),
      };
    }),
  };
}

export interface EntityDetailData {
  kind: string;
  id: string;
  name: string;
  /** Resolved locale text for THIS entity, when its contract holds one. */
  description: string;
  /** Mita-keyed accent pair (palette floats → hex); undefined off-mita. */
  accentLocal?: string;
  accentSoftLocal?: string;
  /** Selected client portrait when one exists (art.ts). */
  portrait?: string;
  availableLocales: readonly string[];
  /** The raw contract row — module builders join from here, never re-read. */
  row: Record<string, unknown>;
}

export function buildDetailData(
  kind: string,
  id: string,
  localeCode: string
): EntityDetailData {
  if (!ENTITY_KINDS[kind] || !KIND_SEGMENT[kind]) notFound();
  const row = findRow(kind, id);
  if (!row) notFound(); // unknown slug → 404, never invented
  const locales = availableLocalesFor(kind);
  if (!locales.includes(localeCode)) notFound();
  let description = "";
  if (kind === "mita" || kind === "players") {
    description = resolveLoc(localeCode, (row as unknown as PersonageRow).description_loc);
  }
  return {
    kind,
    id,
    name: displayName(kind, row, localeCode),
    description,
    accentLocal: accentFor(kind, row),
    accentSoftLocal: softAccentFor(kind, row),
    portrait: indexArtFor(kind, row, localeCode),
    availableLocales: locales,
    row,
  };
}

/** Per-entity metadata: unique per locale via the game's own strings. */
export function buildEntityMetadata(
  kind: string,
  id: string,
  localeCode: string
): Metadata {
  const data = buildDetailData(kind, id, localeCode);
  // Self-canonical carries the locale prefix exactly like the serving URL
  // (localization-architecture §1): /ru/mita/x declares /ru/mita/x; the
  // pivot stays bare. A bare canonical on a prefixed page would consolidate
  // every locale into EN.
  const barePath = `/${KIND_SEGMENT[kind]}/${id}`;
  return {
    title: data.name,
    // The entity's own locale text when the contract holds one; the bare name
    // never as boilerplate.
    description: data.description ? metaSentence(data.description) : undefined,
    alternates: {
      canonical: `${getLocale(localeCode)?.prefix ?? ""}${barePath}`,
      // buildAlternates re-prefixes per locale itself — feed it the bare path
      languages: buildAlternates(barePath, data.availableLocales),
    },
  };
}

/**
 * Meta description = the entity's own first sentence(s), capped to a
 * snippet-length cut at a sentence boundary — game text, not composed prose.
 */
export function metaSentence(text: string, max = 280): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  const cut = clean.slice(0, max);
  const lastDot = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("。"));
  return lastDot > 40 ? cut.slice(0, lastDot + 1) : `${cut.trimEnd()}…`;
}
