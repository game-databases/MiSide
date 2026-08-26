import Link from "next/link";

import { Breadcrumbs } from "@/components/chrome/Breadcrumbs";
import { EntityShell } from "@/components/entity/EntityShell";
import { VoidWell } from "@/components/kit/VoidWell";
import {
  displayName,
  desluggedLabel,
  personageById,
  type EntityDetailData,
} from "./entityView";
import {
  kindRows,
  findRow,
  characterAchievementEdges,
  characterSceneEdges,
  minigamesInContainer,
  type CartridgeRow,
  type ProfileDocumentRow,
  type AchievementRow,
  type MinigameRow,
  type EndingRow,
  type SceneRow,
} from "@/data/contracts";
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

  if (data.kind === "mita" || data.kind === "players") {
    const cartridges = kindRows("cartridges").filter(
      (r) => (r as unknown as CartridgeRow).depicts_character_id === data.id
    );
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
                label: displayName("cartridges", r as Record<string, unknown>, localeCode),
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
    const profiles = kindRows("profiles").filter(
      (r) => (r as unknown as ProfileDocumentRow).subject_character_id === data.id
    );
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
                label: displayName("profiles", r as Record<string, unknown>, localeCode),
              };
            })}
          />
        ),
      });
    }

    // Appearances — shipped relink rows only (character--scene-membership);
    // a character the corpus does not place gets no module, never a guess.
    const sceneIds = [
      ...new Set(
        characterSceneEdges()
          .filter((e) => e.from === data.id)
          .map((e) => e.scene_id)
      ),
    ];
    if (sceneIds.length > 0) {
      const sceneRows = sceneIds
        .map((sid) =>
          kindRows("locations").find(
            (r) => (r as unknown as SceneRow).scene_id === sid
          ) as unknown as SceneRow | undefined
        )
        .filter((r): r is SceneRow => Boolean(r));
      if (sceneRows.length > 0) {
        tabs.push({
          id: "appearances",
          label: tabLabel(chrome["nav.locations"], sceneRows.length),
          panel: (
            <ModuleList
              links={sceneRows.map((s) => ({
                href: entityHref(localePrefix, "locations", s.scene_id),
                label:
                  displayName("locations", s as unknown as Record<string, unknown>, localeCode),
                stats: [s.role],
              }))}
            />
          ),
        });
      }
    }

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
      const scene = findRow("locations", container) as unknown as SceneRow | undefined;
      if (scene) {
        tabs.push({
          id: "found-in",
          label: tabLabel(chrome["nav.locations"], 1),
          panel: (
            <ModuleList
              links={[
                {
                  href: entityHref(localePrefix, "locations", scene.scene_id),
                  label: displayName(
                    "locations",
                    scene as unknown as Record<string, unknown>,
                    localeCode
                  ),
                  stats: [desluggedLabel(scene.scene_id)],
                },
              ]}
            />
          ),
        });
      }
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
    const m = data.row as unknown as MinigameRow;
    const achievements = m.achievement_ids
      .map(
        (aid) =>
          kindRows("achievements").find(
            (r) => (r as unknown as AchievementRow).achievement_id === aid
          ) as unknown as AchievementRow | undefined
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
    const e = data.row as unknown as EndingRow;
    if (e.achievement_id) {
      const a = kindRows("achievements").find(
        (r) => (r as unknown as AchievementRow).achievement_id === e.achievement_id
      ) as unknown as AchievementRow | undefined;
      if (a) {
        tabs.push({
          id: "achievement",
          label: tabLabel(chrome["nav.achievements"], 1),
          panel: <AchievementModule rows={[a]} localePrefix={localePrefix} localeCode={localeCode} />,
        });
      }
    }
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

