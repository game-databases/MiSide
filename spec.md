# MiSide — Game Spec (FRAMEWORK §4 template v2.2, DRAFT — unfrozen)

Drafted 2026-08-24 by the Documentator pass (brief S-D1) from the accepted
research wave. Freeze is the orchestrator's call after verifier review;
pre-freeze gaps close per FRAMEWORK §7 step 2 (list at bottom).

Citation shorthands: **D1** =
[docs/research/game-research.mdx](docs/research/game-research.mdx) · **COMP** =
[competitor-research.md](competitor-research.md) · **T1** =
[toolchain.md](toolchain.md) · **DAQ** =
[data-acquisition.md](data-acquisition.md) · **E1** =
[docs/research/explorer-e1-hands-on.mdx](docs/research/explorer-e1-hands-on.mdx) ·
**T2** = [docs/research/ui-style-scout.mdx](docs/research/ui-style-scout.mdx) ·
**PIPE** = [docs/specs/pipeline-run_all.mdx](docs/specs/pipeline-run_all.mdx) ·
**DR** = [_foundation/decision-register.md](../_foundation/decision-register.md).
Locale counts re-measured this pass: 34 client dirs listed directly +
31-entry store `supported_languages` (live keyless appdetails fetch,
2026-08-24; matches the [s1-vB](docs/research/verifications/s1-vB.mdx) recount).

```yaml
game: MiSide                            # AIHASTO (MakenCat: programming/animation, Umeerai: textures/models);
                                        # publishers IndieArk/Shochiku; single-player metafiction-loop horror (D1 §1, §2)
folder: MiSide                          # pack opened [DR-2026-08-24-miside-pack]; client on this host
                                        # A:\SteamLibrary\steamapps\common\MiSide\ (DAQ current state)
tier: TBD (owner D3 call)               # NOT decided in the DR entry; no domain-doctrine §4 roster row yet — owner-only
                                        # ([DR-2026-08-24-miside-pack] ¶1); localhost-first build proceeds regardless
lifecycle: live                         # released 2024-12-10 (D1 §7); newest public release-notes post v0.93L 2025-06-13;
                                        # whether silent later builds changed the in-game string is open until first harvest (D1 §7)
domain: TBD (owner D3 call)             # locale-routing declared now: prefixes, pivot en at bare paths ([DR-2026-08-20-locale-urls])
stack: next                             # default profile §2.20 — chosen because the dialogue-node page mass is unmeasured
                                        # (R-E1-1) and ISR-grade patch ops are wanted; Astro's ≲30k gate cannot be asserted pre-P5

identity:
  steam:                                # field ref: _foundation/live-monitoring.md §4
    apps:
      - { appid: 2527500, role: primary, lifecycle: live, coverage-label: "Steam-connected sessions" }
                                        # full game; installed buildId 19029065, VERSION 0.93L (DAQ; E1 header)
      - { appid: 2527520, role: demo, lifecycle: live, coverage-label: "Steam-connected sessions" }
                                        # demo ends exactly at the ch-3 wardrobe choice (D1 §6) — natural diff boundary;
                                        # NOT installed on any library root (DAQ demo section) — future diff target only
      - { appid: 3404450, role: dlc, lifecycle: live, coverage-label: "Steam-connected sessions" }
                                        # soundtrack DLC (README header; [DR-2026-08-24-miside-pack] ¶1)
    store-cc: us                        # appdetails pulled clean keyless 2026-08-24 (this pass; COMP S5)

locales:                                # §2.4 launch-blocking — three-way reconcile TABLE below (§ Locale strategy)
  official:                             # VERIFIED against client 2026-08-24: 34 dirs under Data\Languages\ (listed this pass;
                                        # matches T1 §4 / E1 step 5) ∩ store 31 (live appdetails fetch = s1-vB recount).
                                        # All 34 ship; last three are client-only (not store-listed):
    [en, ru, uk, be, bg, zh-Hans, zh-Hant, hr, cs, fil, fr, de, hu, id, it, ja, kk, ko, fa, pl,
     pt-PT, pt-BR, ro, sr-Latn, sk, es-419, es-ES, sv, th, tr, vi, ar, ar-EG, ru-x-prerev]
  canonical: en                         # pivot; bare paths, others /xx/ ([DR-2026-08-20-locale-urls])
  ui-locales: []                        # none evidenced — publisher-site languages beyond the client not researched
  community: []                         # none evidenced; RU demand already served officially (both wikis RU-rooted, COMP S2)
  source-per-locale:
    all: client-pack                    # custom loose-file loc system Data\Languages\<locale>\<Category>.txt — line-based
                                        # plain text, ids = category + 0-based line index (T1 §4); join authority PROVEN:
                                        # GlobalLanguage.GetString(name, index) + Localization_UIText.NameFile/StringNumber +
                                        # DataAchievements.lineTranslate verified end-to-end (E1 step 3, step 7)
    filler-policy: explicit-filler      # DECLARED per localization-architecture §5.5: per-locale category skew is real
                                        # (64–76 files/dir, French max — E1 step 5, R-E1-3); a missing category renders the
                                        # localized not-yet-translated filler; a page is omitted only when the entity has ZERO
                                        # strings in that locale — driven solely by extracted/relinks/locale_availability.jsonl
    code-mapping: { Indonesia: id, "Portugues Portugal": pt-PT, "Português-Brasil": pt-BR,
                    ChineseSimplified: zh-Hans, ChineseTraditional: zh-Hant, "Serbian (Latin)": sr-Latn,
                    "Spanish (LatinAmerica)": es-419, "Spanish (Spain)": es-ES, Pre-revolutionaryRussian: ru-x-prerev }
                                        # game-side dir names → BCP-47 (localization-architecture §5.2); patch-note codes
                                        # id/th/hu/ro/sv/es-419 corroborate (D1 §7)
    availability-log: extracted/relinks/locale_availability.jsonl   # regenerated every rerun (localization-architecture §5.4)
  locale-cells: none                    # one worldwide Windows client; no region/era coupling evidenced anywhere in the pack

axes:                                   # §2.18
  version-eras: continuous              # REAL builds only (buildId stamps, appmanifest watch — DAQ update watch);
                                        # the in-fiction version lattice 0.0–1.9 + IDX ids is an ENTITY kind (game_version),
                                        # never a site-era axis — site freshness prints buildId, not Mita-side versions
  platforms: none-declared              # Windows Steam PC only; no console/port evidence in any input
  game-modes: [campaign, peaceful-mode] # Peaceful Mode ships as locked menu stub behind the "Conditions Met" ending
                                        # (D1 §1, §6) — captured under Principle zero as present-but-unreachable data (COMP J11)

# Source shorthands (counts measured in E1 against buildId 19029065):
#   ASSETS = Unity SerializedFile corpus: 51 files / 583,027,900 B + 69 stream siblings (.resS/.resource)
#            / 1,694,288,048 B = 2.277 GB total (E1 step 4); no bundles, no Addressables, NO custom containers (P2 closed)
#   RES    = resources.assets + auto-loaded deps — typed MonoBehaviour home; 993 fully-fielded dumps proven (E1 step 3)
#   LEVELS = level0–23 scene files — dialogue/location/ending/spawner logic home; UNPARSED (R-E1-1, probe P5 next)
#   LOC    = Data\Languages\<locale>\<Category>.txt — 34 dirs, 64–76 categories each, 2,210 txt total (E1 step 5);
#            no trailing newlines → split-based line counting mandatory (E1 step 5 deviation #3)
#   CODE   = Il2CppDumper output: dump.cs 288,102 lines / 6,281 types + DummyDll\ 57 DLLs (E1 step 2) → decompiled
#            trees under extracted/decompiled/ per doctrine (T1 §3)
#   LIT    = stringliteral.json, 619,523 B (E1 step 2)
#   ART    = sprite/tex2d exports incl. per-locale Textures\ (777 png + 3 psd global; subsets differ per locale) (T1 §5, E1 step 5)
#   STEAM  = keyless official surfaces: appdetails, community achievement stats, news RSS (COMP S5)
#   VOICE  = Voice Editor Mono sub-app (Managed DLLs, dnSpyEx-openable) — second source-inventory row, P7 (T1 §1, §2)

entities:                               # seeded from D1 §8 candidate model (marked OUR INFERENCE there); scales are its
                                        # estimates until harvest proves counts — every count is a data-answerable question (rule 8)
  mita_variant:                         # the soul surfaces — see § Page inventory for the page-type mandate
    key: game-id
    attributes: [hosted-version, chapter-appearances, outfits-reflected, portrait, dialogue-set, reboot-behaviour]
    est-scale: "~20–30 (12 main + minor + mention-only)"
    sources:
      - { role: primary, class: client-extraction, container: "RES prefabs + Mita*/DataClothMita* MBs", codec: assetstudiomod-typed-dump,
          readiness: on-disk, readiness-note: "23 Mita* classes catalogued in dump.cs (E1 step 7); field emit = full pull",
          fallback: "T1 §2 primary path", provenance: client, durability: durable }
      - { role: display, class: client-extraction, container: ART, codec: sprite-export, readiness: on-disk,
          provenance: client, durability: durable }
      - { role: reconciliation, class: client-extraction, container: "LOC Personages/Names + LEVELS scene membership",
          codec: loc-line-index, readiness: unverified, readiness-note: "scene membership waits on P5 (R-E1-1)",
          provenance: client, durability: durable }
  player_character:                     # protagonist + Players 1–10 + chibi players + limping person (D1 §2)
    key: game-id
    attributes: [epithet, bio, cartridge-contained-in, chapter-appearances]
    est-scale: "~20"
    sources:
      - { role: primary, class: client-extraction, container: "LEVELS + LOC", codec: loc-line-index+scene-graph,
          readiness: unverified, provenance: client, durability: durable }
  monster_anomaly:
    key: game-id
    attributes: [spawn-scene, trigger-conditions, chapter]
    est-scale: "~10"
    sources:
      - { role: primary, class: client-extraction, container: "LEVELS spawner refs", codec: scene-graph,
          readiness: unverified, readiness-note: "COMP J13 hard spawner refs — P5-dependent", provenance: client, durability: durable }
  chapter:
    key: game-id                        # 20 units 0–19 named like save slots (D1 §1)
    attributes: [title, hosting-mita, locations, save-points, minigames, collectible-set]
    est-scale: "20"
    sources:
      - { role: primary, class: client-extraction, container: "ASSETS levelN ↔ chapter map", codec: scene-graph,
          readiness: unverified, readiness-note: "levelN↔chapter correspondence settles at first level dump",
          provenance: client, durability: durable }
  save_point:                           # load points renamed across patches (Cap→Cappie…) — feeds the changelog viewer (COMP J9)
    key: game-id
    attributes: [name-per-build, chapter-segment, rename-lineage]
    est-scale: "tens [unverified]"
    sources:
      - { role: primary, class: client-extraction, container: LEVELS, codec: scene-graph, readiness: unverified,
          provenance: client, durability: durable }
  game_version:                         # FICTIONAL versions (in-game content, not site eras — see axes)
    key: game-id
    attributes: [idx-id, host-mita, chapters, portal-links]
    est-scale: "~15 (0.0–1.9 known run; IDX 805/809 spoken in dialogue)"
    sources:
      - { role: primary, class: client-extraction, container: "CODE registries + dialogue refs", codec: decompiled,
          readiness: unverified, readiness-note: "COMP J5: authoritative registry replaces the hand-copied blackboard",
          provenance: client, durability: durable }
  location_scene:                       # apartment rooms + transit/version spaces; mirrors loc categories Location 1–14+19 (E1 step 5)
    key: game-id
    attributes: [version, chapters, bounds-shape, pickups, exits]
    est-scale: "~20–40"
    sources:
      - { role: primary, class: client-extraction, container: "LOC LocationHint* + LEVELS", codec: loc-line-index+scene-graph,
          readiness: unverified, provenance: client, durability: durable }
  cartridge_item:                       # 13 character + 10 player cartridges (D1 §3); placement coords replace prose guides (COMP J2)
    key: game-id
    attributes: [depicts-mita, contains-player, exact-placement, chapter, pickup-trigger]
    est-scale: "~23"
    sources:
      - { role: primary, class: client-extraction, container: "RES TamagotchiGame_Cartridge* + LEVELS transforms/triggers",
          codec: assetstudiomod-typed-dump+scene-graph, readiness: unverified,
          readiness-note: "Cartridge classes exist (E1 step 7); coordinates settle at P5", provenance: client, durability: durable }
  profile_document:
    key: game-id
    attributes: [subject-mita, body-text-all-locales, placement, chapter]
    est-scale: "~12 [unverified]"
    sources:
      - { role: primary, class: client-extraction, container: "LEVELS + LOC", codec: loc-line-index+scene-graph,
          readiness: unverified, readiness-note: "COMP J4: full profile text in every locale vs the wiki's EN-only table",
          provenance: client, durability: durable }
  outfit:
    key: game-id
    attributes: [unlock-action, reflected-on, title-screen-override, materials]
    est-scale: "4+ (more teased for Peaceful Mode)"
    sources:
      - { role: primary, class: client-extraction, container: "RES MitaClothesMagic/DataClothMita*", codec: assetstudiomod-typed-dump,
          readiness: on-disk, readiness-note: "families present in the 993-dump census (E1 step 3); bindings = COMP J7",
          provenance: client, durability: durable }
  minigame:
    key: game-id
    attributes: [access-medium, chapter, score-rules, tuning-per-build]
    est-scale: "~17"
    sources:
      - { role: primary, class: client-extraction, container: "RES MinigamesController/Settings + CarSpace_*/MakeManeken_*",
          codec: assetstudiomod-typed-dump, readiness: on-disk,
          readiness-note: "controllers + settings seen in census (E1 step 3)", provenance: client, durability: durable }
      - { role: stats, class: client-extraction, container: CODE, codec: decompiled, readiness: unverified,
          readiness-note: "exact scoring functions (COMP J6) — win thresholds, coin/timer economies", provenance: client, durability: durable }
      - { role: display, class: client-extraction, container: "LOC MiniGame *", codec: loc-line-index,
          readiness: verified, provenance: client, durability: durable }
  achievement:
    key: steam-api-name                 # 26 rows; THREE-WAY JOIN ALREADY PROVEN end-to-end (E1 step 3):
                                        # steamAchievement ↔ icon PPtr<Sprite> pathID ↔ lineTranslate → Achievements.txt line
    attributes: [display-name-all-locales, icon, unlock-condition, type-tag, global-percent]
    est-scale: "26"
    sources:
      - { role: primary, class: client-extraction, container: "RES DataAchievements", codec: assetstudiomod-typed-dump,
          readiness: verified, readiness-note: "26 entries dumped + spot-verified (ACHI_supermegapuperplayer↔line 26 'Pro Gamer')",
          provenance: client, durability: durable }
      - { role: reconciliation, class: official-feed, container: STEAM, codec: none, readiness: verified,
          readiness-note: "global unlock % keyless (rarest 'Pro Gamer' 10.5%); COMP J12 one canonical row per achievement",
          provenance: official, durability: durable }
  ending:
    key: game-id
    attributes: [prerequisites, negative-conditions, safe-window-percentages, unlocks-mode]
    est-scale: "3 (+1 Peaceful-exclusive [planned])"
    sources:
      - { role: primary, class: client-extraction, container: "CODE condition checks + MenuEnding", codec: decompiled,
          readiness: unverified, readiness-note: "COMP J1 flagship derived join incl. negative conditions + 17%/98%/empty windows",
          provenance: client, durability: durable }
  choice_node:
    key: game-id
    attributes: [flag, chapter, polarity, affects-ending]
    est-scale: "tens (only 6 publicly documented)"
    sources:
      - { role: primary, class: client-extraction, container: "CODE + LEVELS flags", codec: decompiled+scene-graph,
          readiness: unverified, provenance: client, durability: durable }
  dialogue_node:
    key: game-id
    attributes: [speaker, chapter, locale-text-x34, node-graph-edges]
    est-scale: "thousands [unverified — set by P5]"
    sources:
      - { role: primary, class: client-extraction, container: "LEVELS DialogueChanger graphs + LOC LocationDialogue*",
          codec: scene-graph+loc-line-index, readiness: unverified,
          readiness-note: "COMP J8: node-keyed, speaker-joined, ALL locales vs the wiki's EN+RU hand-pasted subpages",
          provenance: client, durability: durable }
  travel_gate:                          # portals + devices (ring/necklace)
    key: game-id
    attributes: [source-version, target-version, required-items]
    est-scale: "~10"
    sources:
      - { role: primary, class: client-extraction, container: "CODE teleporter/item configs", codec: decompiled,
          readiness: unverified, readiness-note: "COMP J10", provenance: client, durability: durable }
  secret_easter_egg:
    key: slug
    attributes: [location, trigger, chapter]
    est-scale: "dozens [unverified]"
    sources:
      - { role: primary, class: client-extraction, container: "LEVELS + LIT", codec: scene-graph+literal-scan,
          readiness: unverified, provenance: client, durability: durable }
  debug_command:                        # dev console IS a discovered surface: OpenSettings/OpenFunctions/OpenAddons/
                                        # OpenResources/OpenEditor/OpenLevels/ToggleDebugUnity/OpenData + ConsoleCheats (E1 step 7)
    key: command-name
    attributes: [effect, affected-entities, cheats-flag]
    est-scale: "~10 [unverified]"
    sources:
      - { role: primary, class: client-extraction, container: "CODE ConsoleInterface (#1441)", codec: decompiled,
          readiness: unverified, readiness-note: "COMP J14 maps commands to affected entities", provenance: client, durability: durable }
  game_mode:                            # kind added so COMP J11 maps onto a real kind (s1-vB F9)
    key: mode-id
    attributes: [lock-state, unlock-ending, teased-content]
    est-scale: "2"
    sources:
      - { role: primary, class: client-extraction, container: "ASSETS locked-state scenes + unused animations", codec: mixed,
          readiness: unverified, readiness-note: "Principle zero capture of cut/locked content (COMP J11)",
          provenance: client, durability: durable }

relations:                              # seed = COMP APPLIED DELTA J1–J14 (mandatory relink-floor section, mapped to D1 §8
                                        # families); mechanism tags hard/logic/inferred; inverted indexes emitted per pair
  - "cartridge_item ↔ mita_variant (depicts) AND cartridge_item ↔ player_character (contains) — separate typed edges (hard+logic) [COMP J3]"
  - "cartridge_item ↔ location_scene ↔ chapter via exact transform/pickup-trigger, per buildId (hard) [COMP J2]"
  - "ending ↔ choice_node incl. NEGATIVE conditions + safe progress-windows 17%/98%/empty (logic — flagship derived join) [COMP J1]"
  - "mita_variant ↔ game_version ↔ chapter ↔ IDX ids as registry data, not blackboard prose (hard) [COMP J5]"
  - "minigame ↔ achievement ↔ exact scoring functions (logic) [COMP J6]"
  - "outfit ↔ mita_variant material bindings incl. title-screen override + unlock chain (hard) [COMP J7]"
  - "profile_document ↔ mita_variant ↔ location_scene ↔ chapter ↔ locale (hard) [COMP J4]"
  - "dialogue_node ↔ speaker ↔ locale ↔ chapter — node-keyed, all locales (hard) [COMP J8]"
  - "save_point ↔ chapter + per-build rename lineage → feeds changelog viewer (hard) [COMP J9]"
  - "travel_gate ↔ source/target game_version + required items (logic) [COMP J10]"
  - "game_mode ↔ entity(all kinds) locked/cut-content capture (hard present-but-unreachable + inferred labels) [COMP J11]"
  - "achievement ↔ external-stats(Steam %) ↔ in-game check code — one canonical row (hard defs + capture) [COMP J12]"
  - "monster_anomaly ↔ spawn scene/chapter + trigger conditions (hard spawner refs + logic) [COMP J13]"
  - "debug_command ↔ affected entities (logic) [COMP J14]"
  - "mita_variant ↔ outfit (worn/reflected) — inverse of J7 edge, emitted bidirectionally (hard)"
  - "chapter ↔ location_scene ↔ game_version (hard, scene graph) [D1 §8 family table]"
  - "complete pairwise matrix incl. inferred edges with per-pair status (doctrine Principle one) [DR-2026-08-17-relink]"
  # UI-link coverage map (relink bar #2): every Localization_UIText component is a serialized UI→string link
  # (NameFile+StringNumber, E1 step 3) — the corpus enumerates them wholesale instead of sampling screens.

maps:                                   # §2.6 ESSENTIAL — top-priority workstream; gates SITE-READY not launch ([DR-2026-08-16] ruling 1)
  imagery-path: authored                # interior scene geography; no tile/minimap system evidenced anywhere in the census
                                        # (E1 steps 4/6) → authored scene schematics over CLIENT-DERIVED geometry (FO76/MIR4/PoE2-schematic precedent)
  layers: [apartment-hub,               # the metaspace hub apartment (D1 §1)
           location-scenes,             # per Location* loc family (~14+ rooms + transit spaces)
           version-spaces,              # per-fictional-version floors/zones
           marker-cartridges, marker-profiles, marker-secrets, marker-save-points,
           marker-minigame-access, marker-monsters, marker-travel-gates]
  coordinate-transform: rect-per-map    # assumed per-scene until proven otherwise; derive from one levelN parse first (P5)
  coordinate-sources: { cartridge_item: client, profile_document: client, save_point: client,
                        monster_anomaly: client, minigame-access: client, travel_gate: logic,
                        secret_easter_egg: unknown-P0 }
                                        # all "client" cells = scene transforms/triggers in LEVELS — data-answerable (rule 8),
                                        # gated on the P5 probe; nothing here is proprietary or wiki-sourced
  readiness: ACHIEVABLE                 # coords are provably in-corpus (hard scene data, COMP J2/J13); imagery authored; blocker = P5 parser

economy:
  npc-prices: no                        # shipped build has no purchasable layer; phone shopping is a Peaceful-Mode locked stub
                                        # (D1 §1) — recapture honestly if/when the mode unlocks
  market-feed: none                     # no player economy exists
  streaming: none                       # single-player; no server-side economy surfaces

live:                                   # shapes per _foundation/live-monitoring.md
  steam:
    enabled: yes
    key-ref: shared                     # keyless CCU + news suffice at this scale; graduation on measured need only (D1 D6 template)
    surfaces: [appdetails, news, ccu]
    ccu:
      durability: ephemeral
      history: streaming                 # append-only JSONL from first production poll ([DR-2026-08-15] D1)
      coverage-label: "Steam-connected sessions"
    publish: { artifact: snapshot-json, path: live/steam, history-path: live/steam/ccu.jsonl }
  # catalogue: omitted — single-player, no advertised server list (nothing to census)

tools:                                  # STUB by design — detailed scoring happens in tools-plan.md via the
                                        # site-sections tool-discovery process (≥5 scored ideas REQUIRED before this pack
                                        # counts as tool-planned; D5 launch gate). Candidate lanes, UNSCORED, from the joins above:
  - { name: ending-condition-explorer, type: data-product, evidence: "COMP J1 — nobody models negative conditions/windows" }
  - { name: owned-scene-map, type: planner, evidence: "maps block; Map-Genie-class incumbent ABSENT (COMP negative findings)" }
  - { name: collection-completion-trackers, type: tracker, evidence: "cartridges/profiles/outfits/achievements sets (D1 §3, §5)" }
  - { name: minigame-rule-revealer, type: calculator, evidence: "COMP J6 exact thresholds vs anecdotal guide prose" }
  - { name: dialogue-database-browser, type: data-product, evidence: "COMP J8 — all-locale node-keyed transcripts exist nowhere" }
  - { name: dev-console-command-reference, type: data-product, evidence: "COMP J14 + E1 step 7 console discovery" }

automation:                             # §2.12
  update-trigger: build-id              # appmanifest read + keyless appdetails cross-check (DAQ update watch); rerun =
                                        # ./run_all <path> stages harvest→decompile→loc→art→relink→emit (PIPE)
  patch-cadence: irregular              # four known patches Dec 2024–Feb 2025, silent since v0.93L 2025-06-13 (D1 §7);
                                        # Peaceful Mode announcement keeps the long tail warm (D1 §1)
  staleness-model: per-record           # buildId stamps on every record; rename lineage (J9) and minigame tuning diffs
                                        # prove per-record movement between builds
  watches: [appmanifest-buildid, steam-news-rss, metadata-version-drift, endpoint-death]
                                        # metadata drift = P6 escalation path (T1 §8); news feed pins public patch dates

satellite:                              # §2.17
  platform: none                        # single-player narrative horror exposes no overlay event surface to hook (D1 §1);
                                        # revisit only if Peaceful Mode adds live services
  status: no
  gep-check: done                       # declined structurally, not by omission — no GEP-class events exist to check

legal:                                  # facts + tags only — legality analysis stays owner-domain (AGENTS.md rule 2)
  data: client-derived from the official Steam install on this host (DAQ); Steam keyless public surfaces for
        achievement %/news/appdetails (COMP S5); license tags recorded repo-side at first pull; provenance is
        two-class (AGENTS.md rule 3) — user-facing buildId+coverage only, source identity never ships
  tooling: Il2CppDumper v6.7.46-net6, AssetStudioModCLI 0.19.0.0, UnityPy 1.25.3 pip freeze (E1 steps 1–2);
        ILSpy/dnSpyEx per T1 §3; tool license tags recorded at first pull per doctrine
  fan-program: monitoring               # indie two-person team, active Kickstarter since 2025-10-31 (D1 §7) — eligibility
                                        # watched, business packet prepared at freeze (D6)
  avoid-list: [player-save-data]        # saves are user data; datasets come from client files only — the protocol layer
                                        # inventories the Steam cloud-save surface without ingesting saves (T1 §5 item 4)
  personal-data: none                   # no player names in any planned surface
  malware-policy: n/a                   # acquisition = logged-in Steam client install; no forum/leaked artifacts touched

external-dependencies: [steam-news-rss (News input), steam-keyless-appdetails+ccu (@gamedb/steam collector)]

content-policy-holes:                   # §2.13 + [DR-2026-08-18-media-scope]
  - 3D-ban → character/scene meshes catalogue-first (MagicaBoneCloth/BoneClothMeshData families dominate the MB
    census, E1 step 3) → MEDIA-CATALOGUE.md; no renders on site
  - audio offload → 28,725 .ogg ≈ 1.44 GB is the FIRST catalogue row (E1 step 6, R-E1-5); voice presence survives
    only as per-locale metadata (11 store languages label full audio — measured this pass); no audio ever ships
  - video: none exists in the install (E1 step 6 census) — no hole
  - heavy textures catalogue-first → per-locale Textures (777 png + 3 psd ≈ 26 MB psd alone) + stream siblings
    (largest sharedassets20.assets.resS 368 MB, E1 step 4)
  - GI cache catalogue-only (level3 Enlighten tree, R-E1-4) — never chased, never shipped

missing-data:                           # mirrors future missingdata.md
  - levelN scene corpus unparsed (R-E1-1) — gates dialogue_node/save_point/choice_node scales, cartridge coords,
    spawner refs; P5 probe is the next action (PIPE §next-probes agrees)
  - second loc layer inside assets unprobed (P3 SharedTableData scan)
  - store-vs-client locale delta RESOLVED this pass: 31↔31 exact + 3 client-only (table below) — ledger per-locale
    category deltas (64–76) + texture subset deltas (ja 20 vs en/ru/fr 26) remain open until first full loc pull (R-E1-3)
  - exact counts profiles/secrets/save-points; full choice-flag list (6 publicly documented of presumably many);
    version↔IDX registry completeness; cartridge placement drift across 0.91–0.93L — all data-answerable (D1 §8 closing)
  - demo 2527520 not installed — diff-boundary target only (DAQ)
  - in-game version string vs silent post-v0.93L builds [unverified until harvest]

status: { research: done, spec-frozen: true, adapter: not-started,
          full-pull: done, site: not-started, maps: not-started,
          locales-complete: true, seo-layer: not-started, verified: true }
# research: D1 + COMP double-PASS (s1-vB verdict PASS; fixes applied) · T1/T2 accepted (t2 double-PASS, 32 hexes
# re-verified) · E1 hands-on WORKS×6/PARTIAL×1 · PIPE frozen after R-P1 revision + n2 double-PASS
# spec-frozen flips ONLY on orchestrator ruling after verifier review of THIS file (FRAMEWORK §7 step 2).
# FLIPPED 2026-08-25: A-SD1 ruled SPEC_FROZEN; tools-plan.md landed (R-T-P1 APPROVE → F-TP1 → tp1-vA PASS)
# satisfying A-SD1's sequencing note. full-pull: X-3 EXECUTION COMPLETE (all stages green, x3-vA PASS).
# locales-complete: S5 2,210/2,210 ×34 locales (A-S6 policy). verified: PROOF §5 reconciles all six
# dataset scoreboards (CLOSURE-1, v-c1a+v-c1b PASS).
```

## Product definition & audience

**What this is.** The structured database of MiSide's content universe,
derived from full client deconstruction rather than community transcription.
The niche measurement is stark: beyond two independent Fandom communities (EN
99 non-redirect pages of 140 raw mainspace titles / RU ~89 pages,
COMP S1) and ≥100 linear Steam-guide prose posts, **no
structured MiSide database exists** — no wikily.gg presence, no wiki.gg, no
game8/IGN/Fextralife (COMP negative findings). The incumbents' ceilings are
hand-copied tables (the best relational artifact anywhere is a screenshot of
an in-game blackboard, COMP J5), two-locale transcripts against our 34
(COMP J8), and placement prose that already disagrees with itself
(Ghostly Mita ch 9 vs ch 10, COMP findings). Our product is the applied-delta
join graph (COMP J1–J14): derived from code and registries, refreshable by
rerun, identifier-preserving, and per-build diffable.

**Who it serves.**

- **Completionists** — 26 achievements including missables and two
  collection sets ("Caught Them All", "Hi, Mita") with global-% context
  (D1 §5); trackers make the sets checkable.
- **Ending hunters** — 3 endings whose conditions include *negative*
  requirements and numeric safe-access windows (D1 §6); the ending explorer
  renders the real flag graph, not six prose bullets.
- **Collectors** — 13 character + 10 player cartridges, profile documents,
  outfits with multi-character reflection (D1 §3); exact coordinates replace
  contradicting guide prose (COMP J2).
- **Lore readers** — Players 1–10 bios, monsters, the fictional version
  lattice, and node-keyed dialogue in every locale (D1 §1–2, COMP J8).
- **The RU+EN dual community** — the game's two wiki cultures are separate;
  RU is a first-class audience, and 34-locale coverage makes every other
  language first-class too (§ Locale strategy).
- **Peaceful Mode watchers** — announced, Kickstarter-backed, still locked
  (D1 §1, §7); the locked-stub dataset (COMP J11) is the only honest source
  tracking it.

Scale honesty: this is a small, finite corpus (~250–350 core entities +
thousands of dialogue nodes) — a depth play. The moat is the join graph,
per-build diffs, and total locale coverage, not roster size.

## Section map (CORE / FIT — nothing cut silently)

Per `_foundation/site-sections.md`; every skipped [FIT] carries its
justification inline. Aggressive internal linking is assumed throughout (the
relink graph IS the link graph).

| # | Section | Tag | Shape for MiSide |
|---|---|---|---|
| 1 | Database | **[CORE]** | Entity pages for all §4 kinds; relink-driven cross-linking everywhere (COMP J-edges) |
| 2 | Interactive maps | **[CORE]** (has geography) | **Owned scene maps**: apartment hub + per-location/version-space layers; map module embedded on every placement-bearing entity page; two-way links; URL state (`?focus=kind:slug`) |
| 3 | News | **[CORE]** | Patch/event coverage from the Steam feed (collab, Kickstarter, awards — D1 §7) + per-patch data diffs; site news per UGC mandate |
| 4 | Guides | **[CORE]** | Mechanics explainers grounded in the logic layer: ending routes with real conditions, cartridge routes from coordinates, minigame thresholds — every claim linking to entities (demand: 100+ guides, COMP S3) |
| 5 | Tools | **[CORE]** | Stub → `tools-plan.md` (scoring later; § Tools overview below) |
| 6 | Builds/loadouts | FIT — **skipped** | Narrative horror has no build/loadout systems to model (D1 §1–2); revisit only if Peaceful Mode adds progression |
| 7 | Tier lists/meta | FIT — **skipped** | No competitive meta exists |
| 8 | Trackers & checklists | **[FIT → ship]** | Achievement/cartridge/profile/outfit/secret completion trackers tied to accounts ([DR-2026-08-19-ugc-accounts]); achievement type-tags already in-game (D1 §5) |
| 9 | Events calendar & timers | FIT — **skipped** | Finished single-player title; no rotations/restocks. Peaceful Mode launch lands as News |
| 10 | Leaderboards | FIT — **skipped** | Single-player; no official boards; we never invent rankings |
| 11 | Economy/market | FIT — **skipped** | No player economy; shipped build has no purchasable layer (economy block above) |
| 12 | Media | **[FIT]** | Galleries of permitted classes ONLY: sprites, portraits, per-locale art, screenshots — audio/video/3D never (content-policy-holes) |
| 13 | Lore/story | **[FIT → ship]** | Dialogue database, profile documents, player bios — "dialogue/text databases are content too" (site-sections #13) |
| 14 | Glossary/mechanics ref | **[CORE]** | Version lattice, portal/device rules, formation/reboot mechanics, dev-console verbs rendered for humans |
| 15 | Changelog/version diff | **[CORE differentiator]** | Per-build diffs with real inputs: save-point renames (COMP J9), minigame tuning (0.93 notes, D1 §4), locale additions (D1 §7); `/news/patch/{id}` shape per D5 ambition move 3 |
| 16 | Comments & ratings | **[CORE]** | On entity/guide/tool pages ([DR-2026-08-19-ugc-accounts]) |
| 17 | User corrections | **[CORE]** | Correction queue targeting our data rows (moderation standard per-pack build-time call) |
| 18 | User profiles | **[FIT → ship]** | Saved trackers, favorites, alert settings |
| 19 | LFG/social | FIT — **skipped** | Single-player |
| 19a | User screenshots | **[FIT → ship]** | Signed-in uploads per [DR-2026-08-19-ugc-accounts] item 3 (defaults 10 MB/screenshot, 20/user/day); user-captured media — distinct from row 12's extracted-art galleries |
| 20 | Global search | **[CORE]** | **Header search-in-place** — NO search route exists (`/search` is a 404, absent from header/footer/robots); the header field owns it, results replace page content in place at ≥2 chars ([DR-2026-08-22-search-is-not-a-page], [DR-2026-08-22-inputs-answer-as-you-type]) |
| 21 | Public API + embeds | **[FIT differentiator]** | Static JSON API is already a launch gate (seo-standard §9 machine plane); tooltip widgets/Discord bot = post-launch bundle (D5) |
| 22 | Notifications | FIT — deferred | Nothing timer-shaped to alert on at launch; patch-watch exists as automation; revisit with Peaceful Mode |
| 23 | RSS/feeds | **[CORE-cheap]** | News + patch-diff feeds |
| 24 | SEO infra | **[INFRA]** | hreflang cluster over all shipped locales, per-entity OG cards from owned art, sitemaps per section/locale |
| 25 | PWA/mobile | **[INFRA]** | Responsive mandatory; installable PWA deferred (no timers to power it) |
| 26 | Site changelog/roadmap | **[CORE-cheap]** | Public devlog |
| 27 | Feedback channel | **[CORE]** | Bug/suggestion pipeline |
| 28 | Monetization | Owner's call | Pages composed so surfaces can slot in later (site-sections #28) |

**Per-game extras** (beyond the floor, as the standard invites):

- **Mita character pages as soul surfaces** — the flagship page type. Each
  Mita page re-keys the whole surface to that Mita's palette (colour-is-
  identity, design-standard §5.1; T2 §7.3), hosts her version/chapters/
  cartridges/profiles/outfits/dialogue as joined modules, and treats the
  page itself as a finished object holding both game faces (cozy chrome,
  corruption one hover away — T2 §7.8).
- **Ending explorer** — interactive ending↔condition graph including
  negative conditions and safe windows (COMP J1); also a tool candidate.
- **Locked-content ledger** — Peaceful Mode stubs and cut content presented
  as visible-locked, never invented (COMP J11; honesty-without-apology bar,
  design-standard §5.1).

## Page inventory

Core corpus (entity pages, per D1 §8 scales): mita_variant 20–30 ·
player_character ~20 · monster_anomaly ~10 · chapter 20 · save_point tens ·
game_version ~15 · location_scene 20–40 · cartridge_item ~23 ·
profile_document ~12 · outfit 4+ · minigame ~17 · achievement 26 · ending 3+
· choice_node tens · travel_gate ~10 · secret dozens · debug_command ~10 ·
game_mode 2 → **≈250–350 entity pages**, plus section indexes,
guides, news, glossary, map pages.

**dialogue_node is the scale unknown**: "thousands" per D1 §8, set by the P5
levelN probe (R-E1-1). Naïvely ×34 locales that is six-figure page mass —
and the seo-standard §5 uniqueness floor forbids generating thin per-node
pages regardless. Declared shape: dialogue ships as **data** (static JSON
API + chapter/speaker-scoped browsable views + per-Mita/per-chapter modules
on parent pages); standalone dialogue-node pages exist only where a node
carries unique quotable content. This decision is revisited once P5 fixes
the count.

Stack consequence: `stack: next` (FRAMEWORK §2.20 default) — ISR absorbs
either corpus outcome; the Astro ≲30k-page gate cannot be truthfully
asserted before P5 measures dialogue mass.

## Tools overview (stub — scoring lives in `tools-plan.md`)

Per site-sections tool-discovery process, `MiSide/tools-plan.md` must carry
≥5 evidence-linked, scored ideas before the pack counts as tool-planned
(launch gate, D5). Candidate lanes surfaced by the joins, unscored:
ending-condition-explorer (J1) · owned scene map (maps block; no
Map-Genie-class incumbent exists, COMP negative findings) ·
collection-completion trackers (D1 §3/§5) · minigame-rule revealers (J6) ·
dialogue-database browser (J8) · dev-console command reference (J14 + E1
step 7 console discovery). Moat framing: every candidate derives from data
competitors do not hold (COMP net advantages 1–5).

## Locale strategy

Pivot **en** at bare paths; every other locale fully localized under its
BCP-47 prefix (`/ru/…`, `/pt-BR/…`, regional forks included) — never query
strings, `/{en}/*` URLs do not exist and 301 to bare paths
([DR-2026-08-20-locale-urls]). One page per entity per locale, cross-locale
link row + hreflang cluster driven exclusively by
`extracted/relinks/locale_availability.jsonl`, `x-default` → bare path
(localization-architecture §1–§2). Chrome i18n is a namespace separate from
game text (localization-architecture §4); per-locale unique titles/meta from
the game's own strings (§3, seo-standard §5).

Three-way reconciliation, measured 2026-08-24 (this pass):

1. **Client**: 34 dirs under `A:\SteamLibrary\steamapps\common\MiSide\Data\Languages\`
   (listed directly; identical set to T1 §4 / E1 step 5).
2. **Store**: exactly 31 entries in `supported_languages` (live keyless
   appdetails fetch; confirms the s1-vB recount of 31 and supersedes the
   stale "30" in README/[DR-2026-08-24-miside-pack] ¶4).
3. **Site**: pivot en bare paths, prefixes elsewhere (point 3 of the mandate).

Result: **31↔31 exact match, zero store-only stragglers, plus 3 client-only
dirs** — all 34 ship (FRAMEWORK §2.4 keys off the client, not marketing).

| # | Code | Client dir | Store | Notes |
|---|---|---|---|---|
| 1 | en | English | Y | pivot — bare paths, no prefix |
| 2 | ru | Russian | Y | co-primary community; full audio per store label |
| 3 | uk | Ukrainian | Y | added v0.91 (D1 §7) |
| 4 | be | Belarusian | Y | store-listed; rare tier — parity check at first loc pull |
| 5 | bg | Bulgarian | Y | |
| 6 | zh-Hans | ChineseSimplified | Y | code mapping per localization-architecture §5.2 |
| 7 | zh-Hant | ChineseTraditional | Y | |
| 8 | hr | Croatian | Y | |
| 9 | cs | Czech | Y | |
| 10 | fil | Filipino | Y | |
| 11 | fr | French | Y | largest measured category set (76 files) [E1 step 5] |
| 12 | de | German | Y | |
| 13 | hu | Hungarian | Y | added v0.921 (D1 §7) |
| 14 | id | Indonesia | Y | client dir named "Indonesia"; patch-note code `id` (D1 §7) |
| 15 | it | Italian | Y | added v0.91 (D1 §7) |
| 16 | ja | Japanese | Y | Kana Hanaiwa VO (D1 §2); smallest texture subset (20 png vs EN/RU/FR 26, E1 step 5) |
| 17 | kk | Kazakh | Y | |
| 18 | ko | Korean | Y | |
| 19 | fa | Persian | Y | added v0.924 (D1 §7) |
| 20 | pl | Polish | Y | added v0.91 (D1 §7) |
| 21 | pt-PT | Portugues Portugal | Y | client dir misspells ("Portugues", no ã) — mapping pinned |
| 22 | pt-BR | Português-Brasil | Y | regional fork prefix /pt-BR/ per DR example |
| 23 | ro | Romanian | Y | added v0.921 (D1 §7) |
| 24 | sr-Latn | Serbian (Latin) | Y | store says just "Serbian"; client disambiguates script; added v0.924 (D1 §7) |
| 25 | sk | Slovak | Y | the recount addition — README's "30" predates s1-vB |
| 26 | es-419 | Spanish (LatinAmerica) | Y | patch-note code es-419 (D1 §7); VO added v0.924 |
| 27 | es-ES | Spanish (Spain) | Y | VO added v0.921 (D1 §7) |
| 28 | sv | Swedish | Y | added v0.921 (D1 §7) |
| 29 | th | Thai | Y | added v0.921 (D1 §7) |
| 30 | tr | Turkish | Y | Turkish VO v0.93 (D1 §7) |
| 31 | vi | Vietnamese | Y | added v0.91 (D1 §7) |
| 32 | ar | Arabic | **N** | client-only — no Arabic entry in store `supported_languages` (measured this pass); per-locale font ships (T1 §4); RTL check at build |
| 33 | ar-EG | Arabic (Egyptian) | **N** | client-only; ties for minimum category set (64 files, E1 step 5) |
| 34 | ru-x-prerev | Pre-revolutionaryRussian | **N** | client-only flavor orthography variant (pre-reform Russian per dir name; contents verified at harvest); private-use BCP-47 subtag |

**Shipping bar.** Site chrome ships for every locale above — all 34 have
client coverage (64–76 category files each). The three client-only locales
are documented, not dropped: they lose only the store-discoverability
expectation, not pages. Per-locale skew (categories 64→76; texture subsets
ja 20 vs en/ru/fr 26) is handled by the declared filler policy + availability
log, and any locale that genuinely fails chrome parity at build gets
ledgered here and in `missingdata.md` — never silently omitted (R-E1-3
demands a present-vs-reference ledger, not an assert-equal). Voice: 11 store
languages label full audio support (measured this pass); the ogg corpus is
offloaded per the media carve-out, so voice survives only as metadata.

## Design direction summary

Full evidence, sampled hexes, and the token table live in
[T2](docs/research/ui-style-scout.mdx) — not duplicated here. The direction,
per its findings:

- **Dark plum-first, never grey** (T2 §5): page field `#140316 → #4a1d5a`
  purple; the purple constant is what keeps this off generic-dark-wiki
  territory (T2 §7.1).
- **Dual-register identity**: cozy candy-pink pill chrome over purple space,
  with the horror face (alarm red `#fc0f43`, CRT green `#08cb05`, VHS
  banding) held as *state treatments*, never decoration — corruption hovers
  mark compromised/glitched entities, red marks danger rows, CRT green is
  the machine voice for buildId/provenance stamps (T2 §4, §7.5; provenance
  per AGENTS.md rule 3 user-facing class).
- **Pill-and-rounded geometry** as the component grammar — radius family
  full/24px/14px; sharp corners read as someone else's site (T2 §3, §7.2).
- **Component kit: shadcn/ui heavily used and upgraded, not reskinned** —
  interactions, animations, and motion rebuilt to the game's own UI
  behaviours (dialogue-box cadence, keycap chips, gradient pills) per
  [DR-2026-08-24-miside-pack] ¶3; stock shadcn look fails the feel bar.
- **Mita-keyed colour souls** on character pages (design-standard §5.1;
  T2 §7.3); cartridge-card grid language for any grid-of-entities page
  (T2 §7.4); checkerboard-void pattern for honest empty wells (T2 §4.5,
  §7.5); keycap `kbd` styling as the keyboard-hint language (T2 §7.7).
- Typography impression: rounded bold sans, uppercase section headers,
  pixel font reserved for machine-voice data; no text below the 12px floor
  (T2 §2; design-standard §3).
- Every page type judged against the design-standard §5 feel bar — Enka
  feel + NWG structure + owned map ([DR-2026-08-22-enka-feel-soul],
  [DR-2026-08-20-design-bar]).

## Data-source map (extraction artifact → site surface)

| Site surface | Feeding artifact(s) | Join / mechanism |
|---|---|---|
| All entity names + display text ×34 locales | `LOC` → `extracted/localization/<locale>/<category>.jsonl` | `GetString(category, lineIndex)` — proven end-to-end (E1 step 7) |
| Achievement pages + trackers | `RES` DataAchievements (26 rows) + `STEAM` stats | three-way hard join: steamAchievement ↔ icon pathID ↔ lineTranslate (E1 step 3) + global % (COMP J12) |
| Mita character pages | `CODE` Mita* class census, `ART` portraits, `LOC` Personages/Names, `LEVELS` scene membership | prefab hard refs + scene membership (E1 step 7) |
| Cartridge placements + map markers | `LEVELS` transforms/pickup triggers | hard coordinates per buildId (COMP J2) |
| Ending explorer / endings | `CODE` condition checks + `LEVELS` flags | logic — flags incl. negatives (COMP J1); MenuEnding surface (E1 step 7) |
| Minigame pages | `RES` MinigamesController/Settings + `LOC` MiniGame* + `CODE` | controllers dumped (E1 step 3); exact scoring = decompiled (COMP J6) |
| Outfit bindings | `RES` MitaClothesMagic/DataClothMita* | material/renderer refs (COMP J7) |
| Dialogue database | `LEVELS` DialogueChanger graphs + `LOC` LocationDialogue* ×34 | node-keyed, speaker-joined (COMP J8); scale set by P5 |
| Save points + changelog viewer | `LEVELS` checkpoint configs per build | rename lineage (COMP J9) |
| Version lattice / glossary | `CODE` registries + dialogue IDX refs | registry-as-data (COMP J5) |
| Travel gates | `CODE` teleporter/item configs | logic (COMP J10) |
| Locked-content ledger | `ASSETS` locked scenes + unused animations | Principle-zero capture (COMP J11) |
| Dev-console reference | `CODE` ConsoleInterface + `LIT` literals | handler decompile (E1 step 7, COMP J14) |
| Icons, OG cards, map markers | `ART` sprite/tex2d exports (incl. per-locale Textures) | versioned CDN paths (FRAMEWORK §2.5) |
| News | `STEAM` news RSS | official feed pins patch dates (D1 §7) |
| CCU gauge + history | `@gamedb/steam` collector | ephemeral/streaming planes, never static JSON (live block) |
| Voice-line conventions (metadata only) | `VOICE` Mono assemblies | second source-inventory row (P7, T1 §1) |
| Never a surface | ogg audio, 3D meshes, GI cache, psd masters | media carve-out + catalogue-first (content-policy-holes) |

## Non-goals

- **No datamined video, 3D models, or audio — ever** (FRAMEWORK §2.13);
  catalogue/offload per [DR-2026-08-18-media-scope].
- **No third-party map embeds** — owned scene maps or none (launch-gate
  negative grep, FRAMEWORK §8).
- **No invented content for locked modes** — Peaceful Mode ships as
  visible-locked captured stubs with developer-attributed teasers cited;
  speculation is not a data class (COMP J11; GW3 concept-entity guardrails
  are the analogy, not a license).
- **No real-world staff/dev entities in the database** — credits live on an
  about/news surface; the DB models the game's world (wiki's developer
  statements stay a News/research input, not an entity kind).
- **No fan-lore authoring in data rows** — every factual claim traces to
  `extracted/` evidence; community lore appears only through UGC surfaces
  (comments/corrections), clearly user-authored (site-sections rules).
- **No mod hosting/modding-guide competition** — modding is a community
  ecosystem (COMP S3); out of product scope.
- **No keyed Steam endpoints** without per-site graduation on measured need
  ([DR-2026-08-15] D1); keyless surfaces cover every declared need today.
- **The fictional version lattice never masquerades as site freshness** —
  site versions print real buildIds; in-fiction versions are content.

## Spec gaps (close before freeze — FRAMEWORK §7 step 2)

1. **P5 levelN probe** — one scene dump to fix dialogue_node /
   save_point / choice_node scales, confirm cartridge-coordinate extraction,
   and size the map transform work (R-E1-1; PIPE next-probes agree).
2. **P3 SharedTableData scan** — rule a second loc layer in or out before
   the loc contract freezes (toolchain probe list).
3. **`tools-plan.md`** — ≥5 scored ideas via the tool-discovery process
   (launch gate; this spec deliberately stubs it).
4. **Tier/domain owner call (D3) — HARD FREEZE GATE** — owner-only
   ([DR-2026-08-24-miside-pack] ¶1); question queue carries it;
   `spec-frozen` flips only after the owner rules; roster row lands only
   when tier leaves provisional.
5. **Demo install decision** — worth installing as the demo/full diff
   boundary, or defer until a patch actually lands (DAQ).
6. **Filler-policy validation** — confirm the declared explicit-filler
   policy against real per-locale skew after the first full loc pull
   (R-E1-3 ledger shape).
7. **In-game version string vs silent builds** — settle whether anything
   shipped after v0.93L changed data (D1 §7 `[unverified]`).
8. **Arabic/ar-EG/prerev-ru parity check** — first loc pull confirms the
   three client-only locales meet the same bar as store locales (§ Locale
   strategy shipping bar).
