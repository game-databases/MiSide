import Link from "next/link";

import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { EntityShell } from "@/components/entity/EntityShell";
import {
  LocationModule,
  type LocationSceneRef,
} from "@/components/entity/LocationModule";
import { RelationCards } from "@/components/entity/RelationCards";
import { MapViewer } from "@/components/map/MapViewer";
import { VoidWell } from "@/components/kit/VoidWell";
import {
  displayName,
  desluggedLabel,
  personageById,
  type EntityDetailData,
} from "./entityView";
import {
  sceneMarkers,
  sceneObjectiveHints,
  scenePoiListing,
  sceneLabel,
  mapChromeStrings,
} from "./mapView";
import {
  kindRows,
  findRow,
  characterAchievementEdges,
  characterSceneEdges,
  documentSceneEdges,
  markerSceneId,
  markers,
  minigameCarrierEdges,
  minigamesInContainer,
  cartridgeBySaveKey,
  type BookRow,
  type CartridgeRow,
  type ProfileDocumentRow,
  type AchievementRow,
  type MinigameRow,
  type EndingRow,
  type SceneRow,
} from "@/data/contracts";
import {
  edgesAnchoringPage,
  relationCardsFor,
} from "@/lib/relations/relationCards";
import { articlesReferencing } from "@/data/articles";
import { KIND_SEGMENT, entityHref } from "@/lib/routes";
import { asRoute } from "@/lib/utils";
import type { Chrome } from "@/i18n/request";

/*
 * Entity detail — the finished-object anatomy (design-standard §5): sticky
 * art card keyed to the entity's own soul colour, quotable answer block fed
 * by the entity's own locale text, and conditional modules joined ONLY on
 * pinned contract columns / shipped relink rows. A module exists only when
 * the entity has that data; empty stays omission, never a sentence.
 */
export function EntityDetailRoute({
  data,
  localeCode,
  localePrefix,
  chrome,
}: {
  data: EntityDetailData;
  localeCode: string;
  localePrefix: string;
  chrome: Chrome;
}) {
  const segment = KIND_SEGMENT[data.kind];
  // The client's own broken surfaces carry the horror register as STATE:
  // present-but-unreachable minigame stubs and the mode-stub ending.
  const compromised =
    (data.kind === "minigames" &&
      Boolean((data.row as unknown as MinigameRow).present_but_unreachable)) ||
    (data.kind === "endings" &&
      (data.row as unknown as EndingRow).kind === "mode-stub");

  return (
    <>
      <Breadcrumbs
        localePrefix={localePrefix}
        segments={[segment, data.id]}
        labels={{
          [segment]: chrome[`nav.${data.kind}`] ?? chrome["nav.lore"],
          [data.id]: data.name,
        }}
        homeLabel={chrome["breadcrumb.home"]}
      />
      <EntityShell
        locale={localeCode}
        kind={data.kind}
        id={data.id}
        name={data.name}
        availableLocales={data.availableLocales}
        accentLocal={data.accentLocal}
        accentSoftLocal={data.accentSoftLocal}
        compromised={compromised}
        card={
          data.portrait ? (
            // eslint-disable-next-line @next/next/no-img-element -- static public asset
            <img
              src={data.portrait}
              alt={data.name}
              width={512}
              height={512}
              className="mx-auto h-auto w-full max-w-64 rounded-md"
              loading="eager"
            />
          ) : (
            <VoidWell className="aspect-square" aria-label={data.name} />
          )
        }
        tabs={buildModules(data, localePrefix, localeCode, chrome)}
        quotable={data.description ? <p>{data.description}</p> : undefined}
      />
    </>
  );
}

/*
 * Conditional modules from pinned columns only — depicts_character_id,
 * subject_character_id, achievement_ids, ending→achievement. Every link is
 * plain <a> href: the crawlable link graph. VC-2 fix #5: each module row
 * carries the joined entity's OWN numbers as machine-voice chips (global %,
 * ids, node counts) and each tab carries its row count — density inside the
 * module, never a bare link list.
 */
function buildModules(
  data: EntityDetailData,
  localePrefix: string,
  localeCode: string,
  chrome: Chrome
): Array<{ id: string; label: React.ReactNode; panel: React.ReactNode }> {
  const tabs: Array<{ id: string; label: React.ReactNode; panel: React.ReactNode }> = [];
  const tabLabel = (word: string, n: number): React.ReactNode => (
    <>
      {word} <span className="font-lcd">{n}</span>
    </>
  );

  // M4 — the location module (map-viewer §7): scene-locked viewer embed on
  // location pages, per-entity "found in" + focus anchors on placement-bearing
  // kinds. Sources are consumed, never derived: markers.jsonl rows, shipped
  // relink families, and the row's OWN pinned placement column.
  if (data.kind === "locations") {
    tabs.push({
      id: "location",
      label: chrome["map.sceneLocked"],
      panel: (
        <LocationsScenePanel
          sceneId={data.id}
          localeCode={localeCode}
          localePrefix={localePrefix}
          chrome={chrome}
        />
      ),
    });
  } else {
    const refs = locationSceneRefs(data.kind, data.id, localePrefix, localeCode);
    const unplacedWell =
      refs.length === 0 &&
      data.kind === "profiles" &&
      (data.row as unknown as ProfileDocumentRow).placement_mechanism !== "placed";
    if (refs.length > 0 || unplacedWell) {
      tabs.push({
        // F-MV4 one-locations-tab law: this is THE locations-bearing module of
        // every non-location entity page — count rides the tab label, the
        // census chips ride chrome-keyed legend labels, and no second
        // "Locations N" ModuleList tab duplicates it below.
        id: "location",
        label:
          refs.length > 0
            ? tabLabel(chrome["nav.locations"], refs.length)
            : chrome["nav.locations"],
        panel: (
          <LocationModule
            scenes={refs}
            localePrefix={localePrefix}
            openMapLabel={chrome["map.openMap"]}
            unplacedLabel={chrome["map.unplaced"]}
            censusLabels={mapChromeStrings(chrome).censusLabels}
          />
        ),
      });
    }
  }

  if (data.kind === "mita" || data.kind === "players") {
    // B-RP1 conversion — cartridges ride the REGISTERED family
    // character--cartridge through edgesAnchoringPage; the old ad-hoc
    // depicts_character_id filter was a frontend join that also missed the
    // player side entirely. Peer anchors are `flashes:<save_key>` resolved
    // through the owning cartridge save_key column; an orphan save_key never
    // renders a row (no-orphan law).
    const cartIds = new Set<string>();
    for (const { peer } of edgesAnchoringPage(
      "character--cartridge",
      data.kind,
      data.id
    )) {
      if (!peer || peer.form !== "flashes:") continue;
      const c = cartridgeBySaveKey().get(peer.id);
      if (c) cartIds.add(c.cartridge_id);
    }
    const cartridges = [...cartIds]
      .map((cid) => findRow("cartridges", cid) as unknown as CartridgeRow | undefined)
      .filter((c): c is CartridgeRow => Boolean(c));
    if (cartridges.length > 0) {
      tabs.push({
        id: "cartridges",
        label: tabLabel(chrome["nav.cartridges"], cartridges.length),
        panel: (
          <ModuleList
            links={cartridges.map((r) => {
              const c = r as unknown as CartridgeRow;
              return {
                href: entityHref(localePrefix, "cartridges", c.cartridge_id),
                label: displayName("cartridges", r as unknown as Record<string, unknown>, localeCode),
                // VC-3 fix #1: reader-meaning chips only — where the flash is
                // found (pinned pickup container → scene title) and which
                // collectible set it belongs to. save_key is machine-plane
                // identity and never renders as copy.
                stats: [
                  pickupSceneTitle(c, localeCode),
                  collectibleSetLabel(c),
                ].filter((s): s is string => Boolean(s)),
              };
            })}
          />
        ),
      });
    }
    // B-RP1 conversion — profiles ride the registered document--character
    // family (the corpus's subject-identity join), not a subject_character_id
    // dataset filter re-derived per page.
    const profileIds = new Set<string>();
    for (const { peer } of edgesAnchoringPage(
      "document--character",
      data.kind,
      data.id
    )) {
      if (peer?.form === "profile_document:") profileIds.add(peer.id);
    }
    const profiles = [...profileIds]
      .map((pid) => findRow("profiles", pid) as unknown as ProfileDocumentRow | undefined)
      .filter((p): p is ProfileDocumentRow => Boolean(p));
    if (profiles.length > 0) {
      tabs.push({
        id: "profiles",
        label: tabLabel(chrome["nav.lore"], profiles.length),
        panel: (
          <ModuleList
            links={profiles.map((r) => {
              const p = r as unknown as ProfileDocumentRow;
              // VC-3 fix #1: no chip — profile rows carry no reader-facing
              // number or set beyond their name (flash_save_key is machine
              // identity; it never renders).
              return {
                href: entityHref(localePrefix, "profiles", p.document_id),
                label: displayName("profiles", r as unknown as Record<string, unknown>, localeCode),
              };
            })}
          />
        ),
      });
    }

    // F-MV4 merge: the old "appearances" ModuleList tab re-listed the SAME
    // character--scene-membership edges the location module above already
    // renders (with the two-way map anchors on top) under a second
    // "Locations N" tab. Collapsed — one locations-bearing tab per page.

    // Collectible-set membership — shipped relink rows only
    // (character--achievement forward edges).
    const achIds = [
      ...new Set(
        characterAchievementEdges()
          .filter((e) => e.from === data.id)
          .map((e) => e.achievement_id)
      ),
    ];
    if (achIds.length > 0) {
      const achRows = achIds
        .map((aid) =>
          kindRows("achievements").find(
            (r) => (r as unknown as AchievementRow).achievement_id === aid
          ) as unknown as AchievementRow | undefined
        )
        .filter((a): a is AchievementRow => Boolean(a));
      if (achRows.length > 0) {
        tabs.push({
          id: "achievements",
          label: tabLabel(chrome["nav.achievements"], achRows.length),
          panel: <AchievementModule rows={achRows} localePrefix={localePrefix} localeCode={localeCode} />,
        });
      }
    }
  }

  // VC-3 fix #2 — cartridges stop being the emptiest detail pages. Modules
  // join ONLY pinned edges, the same pattern the Mita pages use: the row's
  // depicts/contains contract column, its own pickup_ref container joined to
  // the scenes dataset by id, and the minigames that container carries via
  // the shipped minigame--scene-carrier relink. No edge is derived here that
  // the corpus does not ship (AGENTS.md rule 8) — there is no direct
  // cartridge↔minigame join and none is faked; the module rides the two
  // hops the corpus itself pins (pickup container → carrier classes).
  if (data.kind === "cartridges") {
    const c = data.row as unknown as CartridgeRow;
    const subjectId = c.depicts_character_id ?? c.contains_player_id;
    const person = subjectId ? personageById().get(subjectId) : undefined;
    if (person) {
      const kind = person.kind === "mita" ? "mita" : "players";
      tabs.push({
        id: "subject",
        label: tabLabel(chrome[kind === "mita" ? "nav.mita" : "nav.players"], 1),
        panel: (
          <ModuleList
            links={[
              {
                href: entityHref(localePrefix, kind, person.character_id),
                label: displayName(kind, person as unknown as Record<string, unknown>, localeCode),
              },
            ]}
          />
        ),
      });
    }
    const container = c.pickup_ref?.container ?? null;
    if (container) {
      // F-MV4 merge: the old "found-in" ModuleList tab duplicated the scene
      // link the location module already renders (scene anchor + OPEN MAP +
      // census chips). Collapsed — the pickup scene lives only in the
      // location tab now.
      // The minigames the same container carries (shipped relink family
      // minigame--scene-carrier, keyed on the row's own pickup container) —
      // the second pinned hop of VC-3 fix #2. Chips carry where the game is
      // played (the corpus's access_medium, in reader words).
      const games = minigamesInContainer(container)
        .map(
          (mid) =>
            findRow("minigames", mid) as unknown as MinigameRow | undefined
        )
        .filter((m): m is MinigameRow => Boolean(m));
      if (games.length > 0) {
        tabs.push({
          id: "minigames",
          label: tabLabel(chrome["nav.minigames"], games.length),
          panel: (
            <ModuleList
              links={games.map((m) => ({
                href: entityHref(localePrefix, "minigames", m.minigame_id),
                label: displayName(
                  "minigames",
                  m as unknown as Record<string, unknown>,
                  localeCode
                ),
                stats: [desluggedLabel(m.access_medium)],
              }))}
            />
          ),
        });
      }
    }
  }

  if (data.kind === "minigames") {
    // B-RP1 conversion — award binds ride the registered minigame--achievement
    // family (award-site ∪ type-tag, J3), not the row's achievement_ids
    // column restated per page. Null-anchor partials drop out fail-closed.
    const achIds = new Set<string>();
    for (const { peer } of edgesAnchoringPage(
      "minigame--achievement",
      "minigames",
      data.id
    )) {
      if (peer?.form === "achievement:") achIds.add(peer.id);
    }
    const achievements = [...achIds]
      .map(
        (aid) =>
          findRow("achievements", aid) as unknown as AchievementRow | undefined
      )
      .filter((a): a is AchievementRow => Boolean(a));
    if (achievements.length > 0) {
      tabs.push({
        id: "achievements",
        label: tabLabel(chrome["nav.achievements"], achievements.length),
        panel: <AchievementModule rows={achievements} localePrefix={localePrefix} localeCode={localeCode} />,
      });
    }
  }

  if (data.kind === "endings") {
    // B-RP1 conversion — the award achievement rides the registered
    // achievement--ending reverse-index family (id-columns pair).
    const awardIds = new Set<string>();
    for (const { peer } of edgesAnchoringPage(
      "achievement--ending",
      "endings",
      data.id
    )) {
      if (peer?.form === "achievement:") awardIds.add(peer.id);
    }
    const awarded = [...awardIds]
      .map(
        (aid) =>
          findRow("achievements", aid) as unknown as AchievementRow | undefined
      )
      .filter((a): a is AchievementRow => Boolean(a));
    if (awarded.length > 0) {
      tabs.push({
        id: "achievement",
        label: tabLabel(chrome["nav.achievements"], awarded.length),
        panel: <AchievementModule rows={awarded} localePrefix={localePrefix} localeCode={localeCode} />,
      });
    }
  }

  // B-RP1 — relation cards: every remaining registered family that anchors
  // this entity, grouped per family with direction-aware peers, carry-law
  // provenance chips and fail-closed states. Cards exist only when the
  // registry ships an edge for this entity (module omission, never an empty
  // section). The tab label is the machine register ("edges·N") — a database
  // voice, like the LCD role tokens, so no chrome key is fabricated.
  const cards = relationCardsFor(data.kind, data.id, localeCode, localePrefix);
  if (cards.length > 0) {
    const itemCount = cards.reduce((n, c) => n + c.items.length, 0);
    tabs.push({
      id: "relations",
      label: (
        <span className="font-lcd text-xs uppercase tracking-wide">
          edges·{itemCount}
        </span>
      ),
      panel: <RelationCards cards={cards} />,
    });
  }

  // content pipeline M2 reverse module (spec §3.2): "featured in guides/news"
  // — crawlable <a href> in BOTH directions with the article graph. Reads
  // ONLY the emitted registry (never article sources); the link rides THIS
  // locale's admitted cell when one exists, otherwise the pivot path —
  // cross-locale navigation, never a mixed-language page.
  const featured = articlesReferencing(data.kind, data.id);
  if (featured.length > 0) {
    tabs.push({
      id: "featured-in",
      label: tabLabel(chrome["article.featuredIn"], featured.length),
      panel: (
        <ModuleList
          links={featured.map((a) => {
            const own = a.locales[localeCode];
            const cell =
              own && own.path
                ? { path: own.path, title: own.title }
                : a.locales.en && a.locales.en.path
                  ? { path: a.locales.en.path, title: a.locales.en.title }
                  : undefined;
            return {
              href: cell?.path ?? "/",
              label: cell?.title ?? a.title_en,
              stats: [a.type === "guide" ? "guide" : a.type],
            };
          })}
        />
      ),
    });
  }

  return tabs;
}

/**
 * VC-3 fix #1 chips — reader words for pinned columns only.
 * `pickupSceneTitle`: the scene title of the cartridge's own pickup container
 * (chapter name where the client names it, re-spaced id otherwise — the same
 * composition rule as location pages). `collectibleSetLabel`: the set's
 * registry value in reader words. Neither ever falls back to a save_key or
 * any other machine-plane identifier; a row without the data gets no chip.
 */
function pickupSceneTitle(
  c: CartridgeRow,
  localeCode: string
): string | undefined {
  const container = c.pickup_ref?.container;
  if (!container) return undefined;
  const scene = findRow("locations", container) as unknown as SceneRow | undefined;
  if (!scene) return undefined;
  return displayName("locations", scene as unknown as Record<string, unknown>, localeCode);
}

function collectibleSetLabel(c: CartridgeRow): string | undefined {
  return c.collectible_set ? desluggedLabel(c.collectible_set) : undefined;
}

/** Achievement rows with their own numbers: global unlock % as a chip. */
function AchievementModule({
  rows,
  localePrefix,
  localeCode,
}: {
  rows: AchievementRow[];
  localePrefix: string;
  localeCode: string;
}) {
  return (
    <ModuleList
      links={rows.map((a) => ({
        href: entityHref(localePrefix, "achievements", a.achievement_id),
        label: a.display[localeCode]?.name ?? a.achievement_id,
        stats: a.steam.global_percent !== null ? [`${a.steam.global_percent}%`] : undefined,
      }))}
    />
  );
}

/* ------------------------------------------------------------------ */
/* M4 — entity↔map producers (map-viewer §7)                           */
/* ------------------------------------------------------------------ */

/**
 * Per-kind scene sources, consumed not derived:
 *  • mita/players → character--scene-membership forward edges;
 *  • minigames   → minigame--scene-carrier carrier edges;
 *  • books/lore  → document--scene-membership (books ride their own pinned
 *    `consumer_scene` column — a scene FAMILY name, never re-keyed to a
 *    registry id);
 *  • cartridges  → markers.jsonl rows (the emitter's join; no runtime DS-4
 *    rejoin);
 *  • profiles    → markers.jsonl rows, falling back to the row's OWN
 *    `placement` column while M0 is pending; the placement-less three
 *    render the honest unplaced well instead.
 * The four from:null scene-class census rows have NO registry slug and are
 * excluded entirely (rendering a container census as a per-entity fact is
 * prohibited).
 */
function locationSceneRefs(
  kind: string,
  id: string,
  localePrefix: string,
  localeCode: string
): LocationSceneRef[] {
  const focusHref = (focusKind: string, sceneId?: string): string =>
    `${localePrefix}/map?focus=${encodeURIComponent(focusKind)}:${encodeURIComponent(id)}${
      sceneId ? `&scene=${encodeURIComponent(sceneId)}` : ""
    }`;

  if (kind === "mita" || kind === "players") {
    const edges = characterSceneEdges().filter((e) => e.from === id);
    return mergeByScene(
      edges.map((e) => ({
        ref: {
          sceneId: e.scene_id,
          sceneTitle: sceneLabel(e.scene_id, localeCode),
          focusHref: focusHref(kind, e.scene_id),
          mechanism: e.mechanism || undefined,
          status: e.status || undefined,
        },
      }))
    );
  }

  if (kind === "minigames") {
    const edges = minigameCarrierEdges().filter((e) => e.minigame_id === id);
    return mergeByScene(
      edges.map((e) => ({
        ref: {
          sceneId: e.container,
          sceneTitle: sceneLabel(e.container, localeCode),
          focusHref: focusHref("minigames", e.container),
          mechanism: e.mechanism || undefined,
          status: e.status || undefined,
        },
      }))
    );
  }

  if (kind === "lore") {
    const edges = documentSceneEdges().filter(
      (e) =>
        (e.family === "paper_part" || e.family === "novella_surface") &&
        e.document_id === id
    );
    return mergeByScene(
      edges.map((e) => ({
        ref: {
          sceneId: e.container,
          sceneTitle: sceneLabel(e.container, localeCode),
          focusHref: focusHref("lore", e.container),
          mechanism: e.mechanism || undefined,
          status: e.status || undefined,
        },
      }))
    );
  }

  if (kind === "books") {
    // consumer_scene is a scene-family label ("Location House"), NOT a
    // registry scene_id — so no /locations link and no scene param on the
    // focus anchor; the value rides as text, verbatim.
    const row = findRow("books", id) as unknown as BookRow | undefined;
    if (!row?.consumer_scene) return [];
    return [
      {
        sceneId: row.consumer_scene,
        sceneTitle: desluggedLabel(row.consumer_scene) || row.consumer_scene,
        focusHref: focusHref("books"),
      },
    ];
  }

  if (kind === "cartridges") {
    const rows = markers().filter(
      (m) => m.entity_kind === kind && m.entity_slug === id
    );
    return mergeByScene(
      rows.flatMap((m) => {
        const sid = markerSceneId(m);
        if (!sid) return [];
        return [
          {
            ref: {
              sceneId: sid,
              sceneTitle: sceneLabel(sid, localeCode),
              focusHref: focusHref("cartridges", sid),
              mechanism: m.placement?.mechanism,
              status: undefined,
              census: m.instance_census,
            },
          },
        ];
      })
    );
  }

  if (kind === "profiles") {
    const rows = markers().filter(
      (m) => m.entity_kind === kind && m.entity_slug === id
    );
    if (rows.length === 0) {
      // own-row fallback while M0 is pending: DS-5 pins the placement column
      const p = findRow("profiles", id) as unknown as
        | (ProfileDocumentRow & {
            placement?: { container?: string };
          })
        | undefined;
      if (p?.placement_mechanism !== "placed" || !p.placement?.container) {
        return [];
      }
      const sid = p.placement.container;
      return [
        {
          sceneId: sid,
          sceneTitle: sceneLabel(sid, localeCode),
          focusHref: focusHref("profiles", sid),
          mechanism: p.placement_mechanism,
        },
      ];
    }
    return mergeByScene(
      rows.map((m) => {
        const sid = markerSceneId(m);
        return {
          ref: {
            sceneId: sid ?? "",
            sceneTitle: sid ? sceneLabel(sid, localeCode) : "",
            focusHref: sid ? focusHref("profiles", sid) : null,
            mechanism: m.placement?.mechanism,
            status: undefined,
            census: m.instance_census,
          },
        };
      }).filter(({ ref }) => Boolean(ref.sceneId))
    );
  }

  return [];
}

type RefInput = { ref: LocationSceneRef };

/** Dedupe same-scene edges; provenance surfaces when ANY edge bites (F-7). */
function mergeByScene(inputs: RefInput[]): LocationSceneRef[] {
  const byScene = new Map<string, LocationSceneRef>();
  for (const { ref } of inputs) {
    const cur = byScene.get(ref.sceneId);
    if (!cur) {
      byScene.set(ref.sceneId, ref);
      continue;
    }
    byScene.set(ref.sceneId, {
      ...cur,
      mechanism: bitingProvenance(cur.mechanism, ref.mechanism, "hard"),
      status: bitingProvenance(cur.status, ref.status, "modeled"),
    });
  }
  return [...byScene.values()];
}

/** Keep whichever value trips the carry law; ties keep the first. */
function bitingProvenance(a: string | undefined, b: string | undefined, neutral: string): string | undefined {
  if (a && a !== neutral) return a;
  if (b && b !== neutral) return b;
  return a ?? b;
}

/**
 * /locations/[scene_id] panel (M3): the viewer in scene-locked mode above
 * the objective-hint lines and the POI listing grouped by kind — eligible
 * kinds render their classes with instance counts; ineligible classes
 * surface as counted rows only.
 */
function LocationsScenePanel({
  sceneId,
  localeCode,
  localePrefix,
  chrome,
}: {
  sceneId: string;
  localeCode: string;
  localePrefix: string;
  chrome: Chrome;
}) {
  const hints = sceneObjectiveHints(sceneId, localeCode);
  const poiGroups = scenePoiListing(sceneId);
  const eligibleGroups = poiGroups.filter((g) => g.eligible);
  const ineligibleGroups = poiGroups.filter((g) => !g.eligible);
  const chromeStrings = mapChromeStrings(chrome);
  return (
    <div className="flex flex-col gap-5">
      <MapViewer
        mode="locked"
        groups={[]}
        sceneIds={[sceneId]}
        initialSceneId={sceneId}
        markersByScene={{
          [sceneId]: sceneMarkers(sceneId, localePrefix, localeCode),
        }}
        chromeStrings={chromeStrings}
      />

      {hints.length > 0 && (
        <ul className="flex flex-col gap-1">
          {hints.map((h, i) => (
            <li key={i} className="text-sm leading-relaxed">
              {h}
            </li>
          ))}
        </ul>
      )}

      {/* POI listing — list form over poi.jsonl (consumed, never derived).
          F-MV4: group headers print the chrome-keyed kind label; the raw
          token stays on title only. */}
      {eligibleGroups.map((g) => (
        <section key={`e:${g.kind}`} className="flex flex-col gap-1.5">
          <span
            title={g.kind}
            className="w-fit rounded-full border px-3 py-1 font-lcd text-xs uppercase tracking-wide"
            style={{ color: "var(--ms-text-2)" }}
          >
            {chromeStrings.kindLabels[g.kind] ?? g.kind}
          </span>
          <ul className="flex flex-wrap gap-1.5">
            {g.classes.map((c) => (
              <li
                key={c.cls}
                className="inline-flex min-h-11 items-center gap-2 rounded-full bg-secondary px-3 text-xs font-bold text-secondary-foreground"
              >
                {c.label}
                {c.count > 1 && (
                  <span className="font-lcd text-[var(--ms-signal)]">×{c.count}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}

      {/* ineligible classes surface as COUNTED rows — labels stay off */}
      {ineligibleGroups.length > 0 && (
        <section className="flex flex-wrap gap-1.5">
          {ineligibleGroups.flatMap((g) =>
            g.classes.map((c) => (
              <span
                key={`i:${g.kind}:${c.cls}`}
                className="inline-flex min-h-11 items-center gap-2 rounded-full border border-border px-3 font-lcd text-xs text-muted-foreground"
              >
                {g.kind}/{c.cls}
                <span>×{c.count}</span>
              </span>
            ))
          )}
        </section>
      )}
    </div>
  );
}

interface ModuleLink {
  href: string;
  label: string;
  /** Machine-voice stat chips riding the row (ids, percents, roles). */
  stats?: Array<React.ReactNode>;
}

/** Dense module panel: linked name + the row's own stat chips. */
function ModuleList({ links }: { links: ModuleLink[] }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {links.map((l) => (
        <li key={l.href}>
          <Link
            href={asRoute(l.href)}
            className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 rounded-full px-3 py-1.5 text-sm font-bold hover:bg-accent"
          >
            <span className="truncate">{l.label}</span>
            {l.stats && l.stats.length > 0 && (
              <span className="flex items-center gap-1.5">
                {l.stats.map((s, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 font-lcd text-xs text-[var(--ms-signal)]"
                  >
                    {s}
                  </span>
                ))}
              </span>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}

