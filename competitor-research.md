# MiSide — Competitor Research (community relationship-model inventory)

Status: **complete** for the relink-floor bar ([DR-2026-08-17-relink] #3,
[extraction-doctrine.md §Relink bare minimum](../_foundation/extraction-doctrine.md#relink-bare-minimum--three-non-negotiable-bars-owner-2026-08-17)).
Analyzed 2026-08-24 via MediaWiki `api.php` wikitext pulls and direct page
fetches; raw pulls in `tmp/s1-fetch/` (untracked). Companion:
[docs/research/game-research.mdx](docs/research/game-research.mdx) — its §8
candidate model is what this file's applied delta feeds.

## Source inventory

| # | Source | Languages | Entity kinds modeled | Independent? |
|---|---|---|---|---|
| S1 | EN Fandom wiki — <https://miside.fandom.com/> | EN (+ interwiki ru/tr on some pages) | chapters, mita variants, players, locations, minigames, achievements, endings, outfits, profiles, monsters, versions(fictional), dialogues(EN/RU subpages), secrets, real-world companies/events | yes |
| S2 | RU Fandom wiki — <https://miside.fandom.com/ru/> | RU | same families **plus** per-Mita cartridge pages, numbered player pages (Игрок 1–10), standalone version pages | yes (separate community, own structure) |
| S3 | Steam Community guides corpus — <https://steamcommunity.com/app/2527500/guides> (≥100 trend-index titles) | EN/RU/ES/ZH/FR/PT-BR mixed | walkthrough-by-chapter prose; cartridge lists; achievement checklists; outfit unlock lists; modding guides | yes |
| S4 | Wikipedia — <https://en.wikipedia.org/wiki/MiSide> | EN | plot, gameplay frame, development, reception only | yes (tertiary) |
| S5 | Official Steam surfaces — [achievements](https://steamcommunity.com/stats/2527500/achievements), [appdetails](https://store.steampowered.com/api/appdetails?appids=2527500), [news feed](https://store.steampowered.com/feeds/news/app/2527500/) | 31 (store; recount per [s1-vB](docs/research/verifications/s1-vB.mdx)) | achievements + %, patch notes, collab/Kickstarter timeline | primary |

**Negative findings** (web searches, 2026-08-24): no wikily.gg presence
(`wikily.gg/miside` soft-404s to the generic homepage); no wiki.gg community;
no game8 / IGN-wiki / Fextralife MiSide database surfaced in search results.
The market for a structured MiSide database is empty beyond the two Fandom
communities and Steam-guide prose.

---

## S1 — EN Fandom wiki

- URL: <https://miside.fandom.com/> · 140 mainspace titles raw (99
  non-redirects) per the allpages pull ([s1-vA](docs/research/verifications/s1-vA.mdx));
  open MediaWiki API.
- Coverage breadth: widest of any source. Hubs: Campaign (chapters+endings),
  Mitas, Players, Minigames, Achievements, Clothes, Locations, Profiles,
  Monsters & Anomalies, Dialogues (transcription subpages in EN and RU only —
  the hub's other five locale links are redlinks,
  [s1-vB](docs/research/verifications/s1-vB.mdx)), MiSide
  (Fictional) version lattice, Secrets/Easter Eggs, OST, Merchandise,
  Developer Statements/Interviews.

### Relationship model actually surfaced

Rendered as structured tables (links inside cells):

- chapter ↔ character: each chapter named for/hosted by its Mita (Campaign gallery).
- game_version ↔ mita ↔ chapter: three-column blackboard table on
  [MiSide (Fictional)](https://miside.fandom.com/wiki/MiSide_(Fictional)) —
  the single best relational artifact any competitor has.
- location ↔ game_version ↔ chapters: [Locations](https://miside.fandom.com/wiki/Locations)
  table (Name/Gallery/Version/Chapters).
- minigame ↔ achievement ↔ access-medium ↔ chapter:
  [Minigames](https://miside.fandom.com/wiki/Minigames) sortable table.
- achievement ↔ type ↔ unlock-condition ↔ chapter:
  [Achievements](https://miside.fandom.com/wiki/Achievements) numbered table.
- ending ↔ prerequisite ↔ chapter: Campaign §Endings — six named Conditions-Met
  prerequisites with negative conditions, plus safe-access windows keyed to
  upload-progress percentages.
- profile(document) ↔ mita ↔ location ↔ chapter:
  [Profiles](https://miside.fandom.com/wiki/Profiles) four-column table.
- outfit ↔ unlock-action ↔ chapter, plus multi-character reflection note:
  [Clothes](https://miside.fandom.com/wiki/Clothes).
- cartridge ↔ owner-mita: only implicitly (gallery categories like "Character
  Cartridge Images", 12 files).

Exists as prose only: player biographies (Players 1–10 epithets/bios), monster
lore, formation/reboot mechanics, portal/device mechanics, secrets, dialogue
transcripts (flat locale subpages).

### Structural weaknesses

- **Redirect chains**: Story→Chapters→`Campaign#List of Chapters`;
  Collectibles→Profiles; Versions→`MiSide (Fictional)#Versions`. Entry points rot.
- **Case-variant duplicate pages**: Cap-Wearing/Cap-wearing Mita,
  Braided-Hair/Braided Hair Mita, Short-haired/Short Haired Mita,
  Be Candid/Being Candid, The Basement ×3 splits.
- **JS-dependent rendering**: tables use the `table-progress-tracking`
  extension — content degrades without JS; crawlers see partial tables.
- Unofficial names flagged inconsistently (`<small>(Unofficial Name)</small>`
  sometimes present, sometimes not).
- No per-page locales (interwiki ru/tr exist only on a few pages; the rest of
  the 31 store languages absent).
- Ads/analytics on HTML surface (API itself is clean).
- Manual data maintenance everywhere — no evidence any table derives from the
  client; cartridge chapter attributions already conflict internally (Ghostly
  Mita listed ch 9 vs ch 10 page).

## S2 — RU Fandom wiki

- URL: <https://miside.fandom.com/ru/> · ~89 mainspace pages, independent
  community (own naming system, own structure).
- Coverage breadth: chapters (all 20 under Russian names), Mita variants,
  players, versions, peaceful mode, achievements, secrets, development.

### Relationship model actually surfaced

- **cartridge-as-entity**: thirteen dedicated «Флешка …» (flash-drive) pages, one
  per Mita — Флешка Миты, Флешка Доброй, … Флешка Ядро. This is the only
  competitor that makes cartridge↔owner an explicit *page-level* relation;
  the EN wiki buries it in galleries.
- **player-as-entity**: Игрок 1…Игрок 10 individual pages + Хромающий Игрок
  (limping player) + Чиби игроки — matching the cartridge-per-player horror
  mechanic with one page per victim.
- **version-as-entity**: Версия 0, 0.5, 1.0F, 1.1, 1.1F, 1.5, 1.75, 1.9 +
  Цикличная версия (looping version) as standalone pages — finer-grained than
  EN's single table row set.
- character ↔ chapter mapping present in prose and infobox-style links;
  no machine-readable join tables at index level.

### Structural weaknesses

- Heavy title duplication/synonymy: Маленькая Мита vs Мита Маленькая;
  Крипи Мита vs Жуткая Мита vs Уродливая Мита (three names, one variant);
  Призрачная appears twice; Сломанная Мита vs Маленькая Мita overlap.
- Smaller coverage (no minigame/outfit/profile tables found at index level).
- Same platform weaknesses as S1 (MediaWiki redirect culture, JS extensions,
  ad surface), plus no cross-language link fabric to S1 (the two communities
  do not share identifiers).

## S3 — Steam Community guides corpus

- URL: <https://steamcommunity.com/app/2527500/guides> · ≥100 titles on the
  trend index alone (`?numperpage=100&browsefilter=trend` returns 100 unique
  filedetails ids — page cap reached, so the corpus floor is 100;
  [s1-vA](docs/research/verifications/s1-vA.mdx)); languages mixed
  EN/RU/ES/ZH/FR/PT-BR declared in titles.
- Coverage breadth: 100% achievement walkthroughs (multiple per language),
  all-cartridges guides, outfit/clothes guides, secrets compilations,
  Peaceful-Mode jumpscare guides, modding how-tos.

### Relationship model actually surfaced

Representative top guide ([All Cartridges Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3391978782),
updated 2024-12-26): item(cartridge) ↔ location-description ↔ chapter, in
ordered prose lists — 13 character cartridges + 10 player cartridges. Other
guides repeat the pattern for achievements (achievement ↔ chapter ↔ condition)
and outfits (outfit ↔ action ↔ chapter). Score rules appear as thresholds
("4 out of 4", "two rounds", "25 apples").

### Structural weaknesses

- Zero entity model: everything is linear prose; no cross-links between guides;
  no entity pages; duplicated effort per language with divergent facts.
- JS-only interactions (voting, comments), no structured export, no locales as
  URLs (language lives in the title string).
- Staleness: many top guides predate v0.93 fixes (Dec 2024 timestamps) with no
  diff discipline.

## S4/S5 — Wikipedia and official surfaces

Wikipedia contributes verified frame facts only (release dates, dev team,
plot spine, reception) — no entity model. Official Steam surfaces are the
primary verification layer: 26 achievements with global percentages, store
metadata (31 languages, categories), and the news feed that pins every public
patch date (§7 of game-research.mdx). Not competitors, but the fact-check floor
this research cites against.

---

## APPLIED DELTA — joins our database adds because we hold the corpus

Mandatory section ([DR-2026-08-17-relink] #3). Each row: what the best
competitor renders today → the join WE ship, mapped to the candidate relation
family from [game-research.mdx §8](docs/research/game-research.mdx#8-candidate-data-model--our-inference),
with mechanism tag (`hard`/`logic`/`inferred`) and where it comes from in the
client. These become rows of `extracted/relinks/` + `RELATIONS.md`.

| # | Competitor ceiling | Join we add | Family (D1 §8) | Mechanism / client source |
|---|---|---|---|---|
| J1 | S1 keeps ending prerequisites as six prose bullets; negative conditions ("avoid the vent") unmodeled | Full `ending ↔ choice_node` graph: every flag, incl. negative conditions and the safe's progress-window gating (17%/98%/empty), as typed edges with flag ids | ending ↔ choice_node | `logic` — decompiled condition checks (IL2CPP metadata v29 tree) |
| J2 | S1/S3 disagree on cartridge placements by hand; S2 has no placement data at all | Every cartridge ↔ exact scene transform/pickup trigger ↔ chapter, per buildId — replacing prose descriptions with coordinates | cartridge ↔ location_scene ↔ chapter | `hard` — scene graphs + pickup triggers |
| J3 | S2 models cartridge→owner at page level only; nobody links player-cartridges to the player *inside* them | `cartridge ↔ mita_variant` (depicts) AND `cartridge ↔ player_character` (contains) as separate typed relations | cartridge ↔ character/player | `hard` refs + `logic` reveal scripts |
| J4 | S1's Profiles table is manually retyped lore | profile_document ↔ subject-mita hard ref + placement, plus full profile text in all 31 locales (S1's Profiles table is English-only; its Dialogues transcripts cover EN+RU only) | profile ↔ mita ↔ location ↔ chapter ↔ locale | `hard` — loc tables incl. `Data/Languages/<locale>/` |
| J5 | S1's version⇄Mita⇄chapter blackboard is a hand-copied in-game texture | The authoritative version registry itself: version ↔ mita ↔ chapter(s) ↔ IDX ids (805/809…) as data | mita_variant ↔ game_version ↔ chapter | `hard` — registry asset/dialogue ids |
| J6 | S1 tabulates minigames with anecdotal score rules ("beat 4 times out of 4") | Exact scoring functions: win thresholds, coin counts, timer values, per-song DDR scoring, Spacecar nitro/coin economy | minigame ↔ achievement ↔ rule | `logic` — decompiled minigame managers |
| J7 | S1 notes outfits reflect on 4 characters; no per-character binding data | outfit ↔ mita_variant material bindings incl. title-screen override, per-outfit unlock flag chain | outfit ↔ character ↔ unlock-source | `hard` — material/renderer refs |
| J8 | Dialogue transcripts: S1 hosts EN+RU locale subpages (the hub's other five locale links are redlinks), manually pasted | Node-keyed dialogue database across all 31 locales, speaker-joined, chapter-scoped, diffable per patch | dialogue_node ↔ speaker ↔ locale ↔ chapter | `hard` — localization tables |
| J9 | Save-point names known only through patch-note renames | save_point registry per build with rename lineage — feeds the changelog/diff viewer directly | save_point ↔ chapter (+ build history) | `hard` — checkpoint configs |
| J10 | Travel mechanics prose only (portals need "objects that correlate versions") | travel_gate ↔ source_version ↔ target_version graph incl. required battery/correlation items | travel_gate ↔ version ↔ item | `logic` — teleporter/item configs |
| J11 | Nobody models Peaceful Mode beyond a menu stub description | Locked-mode inventory: stub scenes, unused animations (kiss/wake-up cited by devs), teased minigames — captured under Principle zero as cut-content dataset | mode ↔ entity (all kinds) | `hard` (present-but-unreachable state) + `inferred` labels |
| J12 | Achievement global % live on Steam only, disconnected from wiki tables | achievement defs joined to Steam keyless stats (unlock %) AND to in-game check code — one canonical row per achievement | achievement ↔ external-stats ↔ logic | `hard` (defs) + capture layer |
| J13 | Monster/anomaly lore is prose; spawner context undocumented | monster_anomaly ↔ spawn scene/chapter + trigger conditions | monster ↔ location ↔ chapter | `hard` spawner refs + `logic` |
| J14 | Debug console commands exist only in one patch-notes table | command registry with effects/cheats mapped to affected entities (e.g. `triggershow` → trigger volumes) — tooling surface for map/planner work | debug_command ↔ entity | `logic` — decompiled console handler |

### Net structural advantages over every listed competitor

1. **Derived, not hand-copied**: J1/J5/J6 come from code and registries —
   competitors cannot refresh theirs without re-playing the game.
2. **Complete pairwise matrix**: S1's strongest table covers 3 columns; our
   join matrix ships every ordered pair with status per doctrine.
3. **Locale as first-class dimension**: 31 locales per text-bearing entity
   (J4/J8) vs 2 hand-pasted transcript pages.
4. **Per-build diffs**: load-point renames (J9) and minigame tuning (0.93
   notes) prove entity facts move between builds; only extraction gives the
   changelog product real inputs.
5. **Identifiers preserved**: IDX 805/809, internal names (`Cap`, `Be Candid`),
   prefab keys — kept verbatim so every edge above stays reproducible.

## Findings & walls (one line each)

- WebFetch domain verification blocked on this host → served by `curl` +
  MediaWiki `api.php`; no retry walls hit (no challenges encountered anywhere).
- `wikily.gg/miside` returns the generic homepage (soft-404): recorded, moved on.
- Steam schema endpoint needs a key; keyless community stats page suffices.
- Ghostly Mita cartridge chapter attribution conflicts between S1 pages and S3
  (ch 9 vs ch 10) — flagged `[unverified]` in D1 §3; settles at harvest.
