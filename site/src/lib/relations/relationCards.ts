/*
 * Relation-card view models — the ONE presentation router over the join-key
 * registry. Every card consumes joins.familyEdges() (registry-pinned files,
 * grammar-parsed anchors, census-gated); nothing here computes a relation the
 * tree does not ship (data-contracts spec §4.2).
 *
 * Laws implemented here:
 *  • FAMILY GROUPING — cards group by registry family; a family with no
 *    anchor resolving to THIS entity renders no card (module omission, never
 *    an empty section);
 *  • DIRECTION AWARENESS — mirror inverses ship in-file (§4.2 cardinality
 *    law), so a peer seen from both sides collapses into ONE item carrying
 *    both directions (rendered ↔); single-sided edges keep their arrow;
 *  • PROVENANCE CARRY LAW (map-viewer §7 F-7) — mechanism/status ride
 *    verbatim; the chip surfaces whenever mechanism !== "hard" OR
 *    status !== "modeled";
 *  • NO-ORPHAN LAW — a peer links ONLY when the owning dataset's emitted
 *    file confirms its row (findRow through ENTITY_KINDS); everything else
 *    renders as an explicit machine token, never a guessed link;
 *  • FAIL-CLOSED — JSON-null anchors, unknown anchor vocabulary and absent
 *    fields degrade to typed explicit states (raw echo / missing_fields
 *    lines), never blanks and never inventions (spec §7 stub policy);
 *  • DENSITY HONESTY — a family whose unlinked machine tokens exceed
 *    DENSE_TOKEN_LIMIT collapses them into per-form counted rows (the scene
 *    panel's counted-rows precedent): counts stay visible, nothing drops;
 *  • DEDICATED-MODULE EXCLUSIONS — families already surfaced by a dedicated
 *    module stay off the cards so a page never shows the same edge twice.
 *    Exclusions documented inline at PAGE_FAMILIES.
 */
import {
  ENTITY_KINDS,
  cartridgeBySaveKey,
  findRow,
} from "../../data/contracts.ts";
import {
  familyEdges,
  joinRegistry,
  type RelationEdge,
  type RelationEndpoint,
} from "../../data/joins.ts";
import {
  desluggedLabel,
  displayName,
  personageById,
} from "../../components/routes/entityDisplay.ts";
import { resolveLoc } from "../../data/resolveLoc.ts";
import type { LocPointer } from "../../data/contracts.ts";
import { entityHref } from "../routes.ts";

export type RelationItemState = "linked" | "text" | "unresolved";

export interface RelationItemVM {
  key: string;
  label: string;
  /** Locale-prefixed page href; null unless the peer is routed AND confirmed. */
  href: string | null;
  /** How this item renders: linked anchor, machine text, or explicit unresolved. */
  state: RelationItemState;
  /** Direction tokens the corpus ships for this pair ("forward"/"inverse"). */
  directions: string[];
  /** Arrow register: page-as-source →, page-as-target ←, mirrored ↔. */
  arrow: "→" | "←" | "↔" | "·";
  mechanism: string | null;
  status: string | null;
  /** Named explicit-missing states, verbatim (spec §7 rule 1). */
  missingFields: string[];
  /** Machine-vocabulary side tokens (controller class, outfit name, …). */
  extras: string[];
  /** Set when dense unlinked tokens collapsed into this counted row. */
  count?: number;
}

export interface RelationCardVM {
  /** Registry family stem ("document--achievement", …). */
  family: string;
  /** Registry `binds` sentence, verbatim. */
  binds: string;
  /** Registry-measured edge census for the whole family. */
  edgeCount: number;
  items: RelationItemVM[];
}

/** Which registered families surface as cards on which routed page kind. */
interface FamilyRoute {
  family: string;
  /**
   * Which anchor side(s) pin an edge to this page: "from", "to", "any",
   * or an id-columns key ("achievement" / "ending").
   */
  side: "from" | "to" | "any" | "achievement" | "ending";
}

/*
 * Per-page-kind family routing. Families NOT listed are either meta-only
 * (measured absence shipped as data — §4.1 MA rows), owned by a dedicated
 * module, or unroutable on both ends:
 *  • scene membership class (character--scene-membership,
 *    document--scene-membership on placement pages,
 *    minigame--scene-carrier) → the LOCATION module owns every "found in"
 *    surface (map-viewer §7); on location PAGES the three surface here as
 *    inbound cards instead;
 *  • character--achievement / document--character / character--cartridge /
 *    minigame--achievement / achievement--ending on their rich-tab kinds →
 *    those tabs consume the same families directly (B-RP1 conversion);
 *  • character--outfit → ALL four rows carry from:null (COMP J7: reflection
 *    targets unproven) — no character anchor exists, no page may claim it;
 *  • character--dialogue-speaker, cloth-site--outfit,
 *    dialogue-node--encoding-residue → no routed consumer on either end;
 *  • scene--chapter / scene--objective-hints / scene--save-vocabulary /
 *    scene--dialogue-pool → loc-pointer joins owned by the scene panel
 *    (chapter title, objective hints) or machine-plane save vocabulary.
 */
const PAGE_FAMILIES: Record<string, FamilyRoute[]> = {
  mita: [{ family: "dialogue-speaker-theme--character", side: "to" }],
  players: [{ family: "dialogue-speaker-theme--character", side: "to" }],
  cartridges: [],
  // document--minigame measured rows carry controller/paper_part anchors and
  // no minigame: endpoint yet — the family stays routed here so a card lights
  // up the moment the registry grows one endpoint (registry-driven, never guessed).
  minigames: [
    { family: "minigame--outfit-unlock", side: "any" },
    { family: "document--minigame", side: "any" },
  ],
  achievements: [
    { family: "minigame--achievement", side: "any" },
    { family: "document--achievement", side: "any" },
    { family: "character--achievement", side: "any" },
    { family: "achievement--ending", side: "achievement" },
    { family: "achievement--award-site", side: "achievement" },
  ],
  endings: [],
  profiles: [
    { family: "document--character", side: "from" },
    { family: "document--achievement", side: "from" },
  ],
  lore: [
    { family: "document--event-wiring", side: "from" },
    { family: "document--minigame", side: "from" },
  ],
  locations: [
    { family: "character--scene-membership", side: "any" },
    { family: "document--scene-membership", side: "any" },
    { family: "minigame--scene-carrier", side: "any" },
  ],
  books: [],
};

/** Above this many unlinked tokens a card collapses them into counted rows. */
export const DENSE_TOKEN_LIMIT = 12;

/**
 * The carry-law surfacing condition (map-viewer §7 F-7), stated ONCE beside
 * the card machinery that feeds it: surface whenever mechanism !== "hard"
 * OR status !== "modeled". ProvenanceChip renders exactly what this allows.
 */
export function provenanceBites(
  mechanism?: string | null,
  status?: string | null
): boolean {
  return (
    (Boolean(mechanism) && mechanism !== "hard") ||
    (Boolean(status) && status !== "modeled")
  );
}

/* ------------------------------------------------------------------ */
/* Endpoint resolution — anchor form → routed page target              */
/* ------------------------------------------------------------------ */

interface ResolvedPeer {
  /** Routed ENTITY_KINDS key, when the anchor form routes at all. */
  routeKind: string | null;
  /** Id inside the owning dataset (differs from raw for bare slugs). */
  routeId: string | null;
}

/**
 * Anchor-form → owning-dataset identity. Pure registry grammar knowledge —
 * row lookups happen later (the no-orphan check against ENTITY_KINDS rows).
 */
function resolveAnchor(e: RelationEndpoint): ResolvedPeer | null {
  if (e.raw == null) return null; // JSON-null anchor: typed empty state
  switch (e.form) {
    case "achievement:":
      return { routeKind: "achievements", routeId: e.id };
    case "scene:":
    case "container:":
      return { routeKind: "locations", routeId: e.id };
    case "minigame:":
      return { routeKind: "minigames", routeId: e.id };
    case "profile_document:":
      return { routeKind: "profiles", routeId: e.id };
    case "paper_part:":
    case "novella_surface:":
      return { routeKind: "lore", routeId: e.id };
    case "flashes:":
      // cartridge identity rides the owning dataset's own save_key column
      // (reference-by-reference, spec §4.3)
      return { routeKind: "cartridges", routeId: e.id };
    case "controller:":
    case "target:": {
      // "<container>#<pathID>:<Class>" — the leading container is the scene
      // registry id (grammar §4.2); the rest stays machine vocabulary.
      const container = e.id.split("#")[0];
      return container ? { routeKind: "locations", routeId: container } : null;
    }
    case "character:":
      return { routeKind: "character", routeId: e.id };
    case "<bare>":
      // bare forms are character slugs (identity families) EXCEPT the
      // minigame carrier census token "scene-class-family@<container>"
      if (e.raw.includes("@")) return null;
      return { routeKind: "character", routeId: e.raw };
    default:
      // loc:/save_point:/speaker-theme:/outfit:/note:/choice_flag:/prop_family:
      return null;
  }
}

/** Character slugs route to the mita OR players tree via the personage row. */
function characterPageKind(characterId: string): string | null {
  const p = personageById().get(characterId);
  if (!p) return null;
  return p.kind === "mita" ? "mita" : "players";
}

/** Cartridge identity by save_key (owning column; no-orphan enforced). */
function cartridgeForSaveKey(saveKey: string) {
  return cartridgeBySaveKey().get(saveKey);
}

/**
 * Carry-law bite across merged mirror rows: whichever value trips the law
 * wins; ties keep the first (same treatment as the location module).
 */
function bitingProvenance(
  a: string | null,
  b: string | null,
  neutral: string
): string | null {
  if (a && a !== neutral) return a;
  if (b && b !== neutral) return b;
  return a ?? b;
}

interface PeerAccum {
  directions: Set<string>;
  /** The PAGE sat on the row's from/to side (arrow register input). */
  pageAsFrom: boolean;
  pageAsTo: boolean;
  mechanism: string | null;
  status: string | null;
  missingFields: Set<string>;
  extras: Set<string>;
}

function arrowFor(acc: PeerAccum): RelationItemVM["arrow"] {
  if (acc.pageAsFrom && acc.pageAsTo) return "↔";
  if (acc.pageAsFrom) return "→";
  if (acc.pageAsTo) return "←";
  return "·";
}

function parsePeerKey(key: string): RelationEndpoint | null {
  if (key === "<null>") return null;
  const colon = key.indexOf(":");
  return colon > 0
    ? { raw: key, form: `${key.slice(0, colon)}:`, id: key.slice(colon + 1) }
    : { raw: key, form: "<bare>", id: key };
}

/** "target:level4#5051:ObjectDoor" → "level4 · ObjectDoor"; else verbatim. */
function compactToken(raw: string): string {
  const m = /^(?:target|controller):(.*?)#(\d+):(.+)$/.exec(raw);
  if (m) return `${m[1]} · ${m[3]}`;
  return raw;
}

/**
 * Does this endpoint anchor THIS page? Handles every identity spelling:
 * bare character slugs, `character:` prefixes, scene:/container: ids and the
 * scene-class-family@<container> carrier token on location pages.
 */
function matchesPage(
  e: RelationEndpoint | null,
  kind: string,
  id: string
): boolean {
  if (!e || e.raw == null) return false;
  if (e.raw.includes("@")) {
    return kind === "locations" && e.raw === `scene-class-family@${id}`;
  }
  if (e.form === "scene:" || e.form === "container:") {
    return kind === "locations" && e.id === id;
  }
  const resolved = resolveAnchor(e);
  if (!resolved) return false;
  if (resolved.routeKind === "character") {
    return (
      resolved.routeId === id && characterPageKind(resolved.routeId ?? "") === kind
    );
  }
  return resolved.routeKind === kind && resolved.routeId === id;
}

/** Side chip for machine vocab riding the row (outfit names, controller classes). */
function sideChipFor(peer: RelationEndpoint, edge: RelationEdge, localeCode: string): string | null {
  if (peer.form === "outfit:") {
    const loc = edge.scalars.display_name_loc as LocPointer | undefined;
    if (loc && typeof loc.category === "string") {
      const named = resolveLoc(localeCode, loc);
      if (named) return named;
    }
    const en = edge.scalars.display_name_en;
    if (typeof en === "string" && en) return en; // search/API glue register
    return null;
  }
  if (peer.form === "controller:" || peer.form === "target:") {
    const parts = (peer.id ?? "").split(":");
    const cls = parts[parts.length - 1];
    return cls && parts.length > 1 ? cls : null;
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* Card assembly                                                       */
/* ------------------------------------------------------------------ */

/**
 * All relation cards for one entity page, in PAGE_FAMILIES order. Cards with
 * zero anchor-confirming edges are omitted — absence stays omission.
 */
export function relationCardsFor(
  kind: string,
  id: string,
  localeCode: string,
  localePrefix: string
): RelationCardVM[] {
  const routes = PAGE_FAMILIES[kind] ?? [];
  const reg = joinRegistry().families;
  const cards: RelationCardVM[] = [];

  for (const route of routes) {
    const fam = reg[route.family];
    if (!fam) continue; // registry removed the family → nothing to render
    const edges = familyEdges(route.family);
    const peers = new Map<string, PeerAccum>();

    const record = (
      key: string,
      edge: RelationEdge,
      pageWasOn: "from" | "to",
      extra: string | null
    ) => {
      let acc = peers.get(key);
      if (!acc) {
        acc = {
          directions: new Set(),
          pageAsFrom: false,
          pageAsTo: false,
          mechanism: null,
          status: null,
          missingFields: new Set(),
          extras: new Set(),
        };
        peers.set(key, acc);
      }
      acc.directions.add(edge.direction || "id-columns");
      if (pageWasOn === "from") acc.pageAsFrom = true;
      else acc.pageAsTo = true;
      acc.mechanism = bitingProvenance(acc.mechanism, edge.mechanism, "hard");
      acc.status = bitingProvenance(acc.status, edge.status, "modeled");
      for (const m of edge.missing_fields) acc.missingFields.add(m);
      if (extra) acc.extras.add(extra);
    };

    for (const edge of edges) {
      if (route.side === "achievement" || route.side === "ending") {
        if (route.family === "achievement--award-site") {
          // id-columns provenance family: echo the serialized grant site
          if (edge.scalars.achievement_id !== id) continue;
          const site = edge.scalars.award_site as
            | { file?: unknown; level?: unknown; method?: unknown }
            | undefined;
          const label =
            site &&
            typeof site.file === "string" &&
            typeof site.level === "string"
              ? `${site.level} · ${site.file}${
                  typeof site.method === "string" ? ` · ${site.method}` : ""
                }`
              : "award_site: <absent>";
          record(`site:${label}`, edge, "from", null);
          continue;
        }
        // achievement--ending: scalar-keyed pair (no anchors)
        const achId =
          typeof edge.scalars.achievement_id === "string"
            ? edge.scalars.achievement_id
            : null;
        const endId =
          typeof edge.scalars.ending_id === "string"
            ? edge.scalars.ending_id
            : null;
        if (route.side === "achievement" && achId === id && endId) {
          record(`ending:${endId}`, edge, "from", null);
        }
        if (route.side === "ending" && endId === id && achId) {
          record(`achievement:${achId}`, edge, "to", null);
        }
        continue;
      }

      const pageOnFrom =
        (route.side === "any" || route.side === "from") &&
        matchesPage(edge.from, kind, id);
      const pageOnTo =
        (route.side === "any" || route.side === "to") &&
        matchesPage(edge.to, kind, id);
      if (!pageOnFrom && !pageOnTo) continue;

      const peerEnd = pageOnFrom ? edge.to : edge.from;
      const extra =
        peerEnd && peerEnd.raw != null
          ? sideChipFor(peerEnd, edge, localeCode)
          : null;
      record(peerEnd?.raw ?? "<null>", edge, pageOnFrom ? "from" : "to", extra);
    }

    if (peers.size === 0) continue;

    /** Assemble one item from its accumulated mirror rows. */
    const buildItem = (
      key: string,
      acc: PeerAccum,
      label: string,
      href: string | null,
      state: RelationItemState
    ): RelationItemVM => ({
      key,
      label,
      href,
      state,
      directions: [...acc.directions],
      arrow: arrowFor(acc),
      mechanism: acc.mechanism,
      status: acc.status,
      missingFields: [...acc.missingFields],
      extras: [...acc.extras],
    });

    const items: RelationItemVM[] = [];
    for (const [key, acc] of peers) {
      const parsed = parsePeerKey(key);

      if (!parsed || parsed.raw == null) {
        // JSON-null peer anchor — the typed empty state, explicitly rendered
        items.push(buildItem(key, acc, "<null anchor>", null, "unresolved"));
        continue;
      }

      const resolved = resolveAnchor(parsed);
      let routeKind = resolved?.routeKind ?? null;
      let routeId = resolved?.routeId ?? null;

      if (routeKind === "character" && routeId) {
        const mapped = characterPageKind(routeId);
        if (mapped) {
          routeKind = mapped;
        } else {
          // provisional slug outside the built personage namespace
          // (DLG-2 fence): unlinked + explicitly unresolved, never guessed
          items.push(
            buildItem(
              key,
              acc,
              desluggedLabel(parsed.id) || parsed.id,
              null,
              "unresolved"
            )
          );
          continue;
        }
      }

      if (parsed.form === "flashes:") {
        const c = cartridgeForSaveKey(parsed.id);
        if (c) {
          routeKind = "cartridges";
          routeId = c.cartridge_id;
        } else {
          // no cartridge row owns this save_key — orphan, never a link
          items.push(
            buildItem(
              key,
              acc,
              desluggedLabel(parsed.id) || parsed.id,
              null,
              "unresolved"
            )
          );
          continue;
        }
      }

      if (routeKind && routeId) {
        const row = findRow(routeKind, routeId) as
          | Record<string, unknown>
          | undefined;
        if (row) {
          items.push(
            buildItem(
              key,
              acc,
              displayName(routeKind, row, localeCode),
              entityHref(localePrefix, routeKind, routeId),
              "linked"
            )
          );
        } else {
          // no-orphan law: the owning dataset does not confirm the row
          items.push(
            buildItem(
              key,
              acc,
              desluggedLabel(routeId) || routeId,
              null,
              "unresolved"
            )
          );
        }
        continue;
      }

      // machine-plane anchor: verbatim echo, compacted for reading
      items.push(buildItem(key, acc, compactToken(parsed.raw), null, "text"));
    }

    // stable order: linked first, then text, then unresolved; labels ASC
    const rank = { linked: 0, text: 1, unresolved: 2 } as const;
    items.sort(
      (a, b) => rank[a.state] - rank[b.state] || a.label.localeCompare(b.label)
    );

    cards.push({
      family: route.family,
      binds: fam.binds,
      edgeCount: fam.edge_count_measured,
      items: collapseDenseTokens(items),
    });
  }

  return cards;
}

/**
 * Density honesty: past DENSE_TOKEN_LIMIT unlinked tokens (machine anchors
 * like note:xxx), collapse them into per-anchor-form counted rows — the
 * scene panel's counted-rows precedent. Linked and unresolved items always
 * render individually.
 */
function collapseDenseTokens(items: RelationItemVM[]): RelationItemVM[] {
  const tokens = items.filter((i) => i.state === "text");
  if (tokens.length <= DENSE_TOKEN_LIMIT) return items;
  const rest = items.filter((i) => i.state !== "text");
  const byForm = new Map<string, { n: number; sample: RelationItemVM }>();
  for (const t of tokens) {
    const form = t.key.includes("@")
      ? "scene-class-family@"
      : t.key.includes(":")
        ? `${t.key.slice(0, t.key.indexOf(":") + 1)}`
        : "<bare>";
    const cur = byForm.get(form);
    if (cur) cur.n += 1;
    else byForm.set(form, { n: 1, sample: t });
  }
  const collapsed: RelationItemVM[] = [...byForm.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([form, { n }]) => ({
      key: `form:${form}`,
      label: `${form}`,
      href: null,
      state: "text" as const,
      directions: [],
      arrow: "·" as const,
      mechanism: null,
      status: null,
      missingFields: [],
      extras: [],
      count: n,
    }));
  return [...rest, ...collapsed];
}

/* ------------------------------------------------------------------ */
/* Dedicated-tab consumption helper                                    */
/* ------------------------------------------------------------------ */

export interface AnchoredEdge {
  edge: RelationEdge;
  /** Which side of the row the page anchored on. */
  pageWasOn: "from" | "to";
  /** The OTHER endpoint (peer), unparsed-null-safe. */
  peer: RelationEndpoint | null;
}

/**
 * Every registered-family edge whose anchor resolves to THIS page — the one
 * consumption path for dedicated tabs converted off ad-hoc dataset filters
 * (B-RP1): cartridges/subject/profiles/minigame-achievements/ending-
 * achievement all read their family through here, so tab data and card data
 * can never disagree about what the corpus ships.
 */
export function edgesAnchoringPage(
  family: string,
  kind: string,
  id: string
): AnchoredEdge[] {
  const out: AnchoredEdge[] = [];
  for (const edge of familyEdges(family)) {
    if (family === "achievement--ending") {
      // scalar-keyed id-columns pair — no anchors to match on
      const achId = edge.scalars.achievement_id;
      const endId = edge.scalars.ending_id;
      if (kind === "achievements" && achId === id && typeof endId === "string") {
        out.push({
          edge,
          pageWasOn: "from",
          peer: { raw: `ending:${endId}`, form: "ending:", id: endId },
        });
      } else if (kind === "endings" && endId === id && typeof achId === "string") {
        out.push({
          edge,
          pageWasOn: "to",
          peer: {
            raw: `achievement:${achId}`,
            form: "achievement:",
            id: achId,
          },
        });
      }
      continue;
    }
    const onFrom = matchesPage(edge.from, kind, id);
    const onTo = matchesPage(edge.to, kind, id);
    if (onFrom === onTo) continue; // neither side anchors this page
    out.push({
      edge,
      pageWasOn: onFrom ? "from" : "to",
      peer: onFrom ? edge.to : edge.from,
    });
  }
  return out;
}
