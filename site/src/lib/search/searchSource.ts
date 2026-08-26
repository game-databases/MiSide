/*
 * THE server-side search-row builder. One construction path over the contract
 * readers — emit-artifacts.mjs imports THIS module instead of re-rolling a
 * private KINDS table, so the emitted per-locale indexes cannot drift from
 * what the readers serve (the B-RP1 re-pin; spec §6 one-matching-function
 * already pinned the query side).
 *
 * Row law:
 *  • rows derive from ENTITY_KINDS reader output only — never bespoke queries;
 *  • locale admission rides the availability ledger exactly like the routes
 *    (a row may never point at a URL that 404s: kindAvailable is the same
 *    gate buildIndexData/buildDetailData notFound() on);
 *  • a row whose title resolves empty in a locale is omitted THERE (declared
 *    omission half of the filler policy) — the index holds named entities,
 *    never raw ids dressed as titles;
 *  • the pivot census is pinned against entities.json (contracts/registry)
 *    via expectedSearchCensus()/assertSearchCensus() — dataset growth without
 *    a registry bump fails the emit.
 */
import {
  ENTITY_KINDS,
  dialogueLevelNodeCounts,
  kindRows,
  scenes,
} from "../../data/contracts.ts";
import { entitiesRegistry } from "../../data/joins.ts";
import { kindAvailable } from "../../data/availability.ts";
import { resolveLoc } from "../../data/resolveLoc.ts";
import { displayName, personageById } from "../../components/routes/entityDisplay.ts";
import { KIND_SEGMENT } from "../routes.ts";
import { LOCALES, getLocale } from "../../i18n/locales.ts";
import type { SearchRow } from "./searchRows.ts";

export type { SearchRow };

/** Kinds in the index, in emission order — the routed entity kinds + the routed dialogue transcript views. */
export const SEARCH_KINDS: readonly string[] = [
  ...Object.keys(ENTITY_KINDS),
  "dialogue",
];

/** A row exists for `kind` only when the owning route would serve it. */
function searchable(kind: string, row: Record<string, unknown>): boolean {
  if (kind === "locations") {
    // boot/menu/title containers have no human name anywhere: not searchable
    return Boolean((row as { chapter_name_loc?: unknown }).chapter_name_loc);
  }
  return true;
}

/** Reader-derived text body for a row (empty when the corpus holds none). */
function searchText(
  kind: string,
  row: Record<string, unknown>,
  localeCode: string
): string {
  const r = row as {
    description_loc?: unknown;
    lore_loc?: unknown;
    depicts_character_id?: unknown;
  };
  if (r.description_loc) {
    return resolveLoc(localeCode, r.description_loc as Parameters<typeof resolveLoc>[1]);
  }
  if (r.lore_loc) {
    return resolveLoc(localeCode, r.lore_loc as Parameters<typeof resolveLoc>[1]);
  }
  // cartridges carry no client display-name table (cartridges contract DS-4
  // rule 2: the save_key IS the label) — the depicted character's name is the
  // honest human text that makes them findable.
  if (kind === "cartridges" && typeof r.depicts_character_id === "string") {
    const dep = personageById().get(r.depicts_character_id);
    if (dep) return resolveLoc(localeCode, dep.name_loc) || dep.character_id;
  }
  return "";
}

/**
 * All rows for ONE locale — entity kinds first (registry order), then the
 * routed /dialogue/<level> transcript views (titles ride scene chapter names;
 * carriers the scenes dataset does not name stay OUT — the same predicate
 * locations use). Availability-gated per kind against the ledger.
 */
export function buildSearchRowsForLocale(code: string): SearchRow[] {
  const def = getLocale(code);
  if (!def) throw new Error(`Unknown locale: ${code}`);
  const rows: SearchRow[] = [];
  for (const kind of Object.keys(ENTITY_KINDS)) {
    if (!kindAvailable(code, kind)) continue;
    // rows speak the URL-SEGMENT vocabulary ("lore/profiles"), the same axis
    // the header facet chips filter on — NOT the raw registry kind key
    const segment = KIND_SEGMENT[kind];
    if (!segment) throw new Error(`routed kind without URL segment: ${kind}`);
    const idField = ENTITY_KINDS[kind].idField;
    for (const row of kindRows(kind) as Array<Record<string, unknown>>) {
      if (!searchable(kind, row)) continue;
      const title = displayName(kind, row, code);
      if (!title) continue;
      const id = String(row[idField]);
      rows.push({
        id,
        kind: segment,
        title,
        text: searchText(kind, row, code),
        url: `${def.prefix}/${segment}/${id}`,
      });
    }
  }
  // dialogue transcript views — every carrier level with a client chapter name
  const nodeCounts = dialogueLevelNodeCounts();
  const chapterByScene = new Map(
    scenes().map((s) => [s.scene_id, s.chapter_name_loc ?? null])
  );
  for (const [lvl, nodeCount] of [...nodeCounts.entries()].sort()) {
    const ch = chapterByScene.get(lvl);
    if (!ch) continue;
    rows.push({
      id: lvl,
      kind: "dialogue",
      title: resolveLoc(code, ch),
      text: `nodes:${nodeCount}`,
      url: `${def.prefix}/dialogue/${lvl}`,
    });
  }
  return rows;
}

/** Every locale's rows, keyed by BCP-47 code (emission order = locale table). */
export function buildAllLocaleSearchRows(): Map<string, SearchRow[]> {
  const out = new Map<string, SearchRow[]>();
  // LOCALES rows are LocaleDef OBJECTS (code/dirName/dir/prefix) — the old
  // emitter's private [code, dirName, prefix] tuples died with it.
  for (const l of LOCALES) out.set(l.code, buildSearchRowsForLocale(l.code));
  return out;
}

/* ------------------------------------------------------------------ */
/* Census pin — the emitted rows must reconcile with entities.json     */
/* ------------------------------------------------------------------ */

/**
 * Expected PIVOT-row census per indexed kind, derived FROM the registry:
 *  • exact counts come from entities.json row_count / enum partitions of the
 *    owning artifact;
 *  • locations and dialogue are searchable SUBSETS of their artifacts (only
 *    chapter-named members), so they pin as bounded counts.
 */
export function expectedSearchCensus(): Record<
  string,
  { exact?: number; max?: number }
> {
  const reg = entitiesRegistry();
  const enumSum = (
    type: string,
    field: string,
    values: string[]
  ): number | undefined => {
    const e = reg[type]?.enums?.[field];
    if (!e) return undefined;
    return values.reduce((acc, v) => acc + (e[v] ?? 0), 0);
  };
  const worldDoc = reg.world_document?.enums?.family;
  const paperParts = (worldDoc?.paper_part ?? 0) + (worldDoc?.novella_surface ?? 0);
  const mitaEnum = reg.personage?.enums?.kind ?? {};
  // keyed by URL SEGMENT — the vocabulary rows carry
  return {
    mita: { exact: mitaEnum.mita },
    players: { exact: mitaEnum.player },
    cartridges: { exact: reg.cartridge_item?.row_count },
    minigames: { exact: reg.minigame?.row_count },
    achievements: { exact: reg.achievement?.row_count },
    endings: { exact: reg.ending?.row_count },
    "lore/profiles": { exact: reg.profile_document?.row_count },
    "lore/books": { exact: reg.book?.row_count },
    // routed lore = paper_part + novella_surface (notes never route)
    lore: { exact: paperParts > 0 ? paperParts : undefined },
    // searchable subset of the 24-scene registry
    locations: { max: reg.scene?.row_count },
    // transcript views ⊆ the registry's dialogue_graph carriers
    dialogue: { max: reg.dialogue_graph?.row_count },
  };
}

/**
 * Fail-loud reconciliation (call at emit time): the PIVOT locale's per-kind
 * distinct-id census must equal the registry expectation, and every other
 * locale's id-set must be a subset of the pivot's (locale omission is legal,
 * locale invention is not).
 */
export function assertSearchCensus(allRows: Map<string, SearchRow[]>): void {
  const expected = expectedSearchCensus();
  const pivotCode = LOCALES[0].code;
  const pivot = allRows.get(pivotCode);
  if (!pivot) throw new Error("search census: pivot locale missing");
  const countByKind = new Map<string, Set<string>>();
  for (const r of pivot) {
    const set = countByKind.get(r.kind) ?? new Set<string>();
    set.add(r.id);
    countByKind.set(r.kind, set);
  }
  for (const [kind, want] of Object.entries(expected)) {
    const got = countByKind.get(kind)?.size ?? 0;
    if (want.exact !== undefined && got !== want.exact) {
      throw new Error(
        `search census (${pivotCode}): ${kind} holds ${got} rows but entities.json pins ${want.exact}`
      );
    }
    if (want.max !== undefined && got > want.max) {
      throw new Error(
        `search census (${pivotCode}): ${kind} holds ${got} rows, above the ${want.max}-row registry bound`
      );
    }
  }
  // locations must equal their reader-derived searchable subset exactly
  const namedScenes = scenes().filter((s) => s.chapter_name_loc).length;
  const gotLocations = countByKind.get("locations")?.size ?? 0;
  if (gotLocations !== namedScenes) {
    throw new Error(
      `search census: locations ${gotLocations} != chapter-named scenes ${namedScenes}`
    );
  }
  // every other locale's id-set ⊆ pivot's id-set
  for (const [code, rows] of allRows) {
    if (code === pivotCode) continue;
    for (const r of rows) {
      const known = countByKind.get(r.kind);
      if (!known || !known.has(r.id)) {
        throw new Error(
          `search census: ${code} carries row ${r.kind}:${r.id} absent from the pivot index`
        );
      }
    }
  }
}
