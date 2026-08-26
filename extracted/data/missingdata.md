# missingdata.md — MiSide consolidated missing-data ledger

Assembled at **CLOSURE-1 phase-1 closure** (2026-08-25) over the six accepted
datasets + their specs. Build pin: **buildId 19029065, VERSION 0.93L** (Unity
2021.3.35f1, IL2CPP). Every entry sweeps a `[unverified]` / stub /
pending-curation / parked mark that lives in `extracted/data/*/`,
`contracts/dataset-*.mdx`, or `docs/specs/dataset-*.mdx`; nothing here is new
deficiency — it is the one ledger the per-dataset honesty READMEs feed
(spec AC-10 pattern).

**Classes:** `owner-call` = needs an owner/research decision or costed tooling;
`derivable-later` = mechanical from the corpus once a named stage/pass runs;
`measured-absence` = the client measurably lacks it — recorded so nobody chases
it. Per AGENTS rule 8 every gap is a dataminer work item, never a frontend guess.

## Cross-cutting

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| XC-1 | IL2CPP native method bodies (decompiled trees are IL-stubs) | Il2CppDumper/ilspycmd emit signatures only | Native decompile pass over `GameAssembly.dll` (Ghidra/IDA-class; new toolchain row, owner-costed — spec A.5.1 defers the cost/benefit call to the owner) | owner-call |
| XC-2 | level↔chapter map (SPEC gap #1) | Level files carry no chapter identity beyond `Scene_Load.stringFileNamePart` | P5-family scene-hierarchy stage; then fills `chapter` columns on profiles/dialogue/scenes and `joins.chapter_attribution` | derivable-later |
| XC-3 | Transform coordinates for pointer-only placements (76 POI rows) + cross-container pathID resolution | Harvest captured type-id-114 assets only; `Trigger_Teleport_#10938→Transform 6192` proves the targets exist undumped (DS-6 §2.6b) | PIPE S9 `scene-transform` UnityPy walk + global pathID index; flips rows without schema change | derivable-later |
| XC-4 | sprite-pathID→export-name index (DS-5 R5) | Art export holds 72,115 sprites by name only | One UnityPy pass (emit stage builds it); unblocks note-text carrier proof + book scene bindings | derivable-later |
| XC-5 | Map markers (`markers.jsonl` ships `_meta` only) | No-orphan rule: owning datasets were in flight at DS-6 build time | Re-run projection now that DS-4/DS-5 landed (cartridge/save-point legs); monster & save-point entity owners still don't exist | derivable-later |
| XC-6 | PIPE stage registration of all six emitters/checkers (+ relink relocation commit discipline) | Builder write scopes excluded `pipeline/stages/` | Orchestrator registration commit carrying the arbiter fences (ds456 agenda-1 DS-4 §1 restatement; A-DS456 DS-5 §1.2 citation + §9 ordering; DS-6 §2.7 dedupe citation) | derivable-later |
| XC-7 | `extracted/RELATIONS.md` pairwise roll-up (doctrine output) | Pair edges are shipped per-pair; the ordered-pair matrix catalog is not yet written | Generated at PIPE stage registration from `relinks/_assembly-provenance.jsonl` + the pair files | derivable-later |
| XC-8 | Protocol layer content (PROOF §4 placeholder) | Single-player title owes proof-of-no-surface or an inventory of Steam/cloud/telemetry surfaces | Bounded inventory pass (achievements/cloud-save endpoints already touched by DS-2 Steam capture) | derivable-later |
| XC-9 | Demo (2527520) diff boundary | No demo install exists on any library (checked 2026-08-24) | Owner installs via logged-in Steam client (questions.md Q2), then diff pass vs full build | owner-call |
| XC-10 | Post-0.93L drift watch | Silent rebuilds could shift registries/indices | buildId stamps everywhere + appmanifest watch rerun; instrument exists, no action now | measured-absence |
| XC-11 | Localized achievement descriptions | Client carries names only; descriptions are keyless Steam community stats | Keyed schema endpoint — deliberate hole until per-site graduation | owner-call |
| XC-12 | Peaceful Mode real dataset (locked stub row only) | Mode not in this build; tamagotchi surfaces flagged `present_but_unreachable` | Patch-day rerun diffs the set mechanically | derivable-later |

## characters (DS-1)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| CH-1 | Version-sign text (44 `Localization_UIText` `NameFile="Version"` links, no `Version.txt` in any of 34 locales) | UI link with no data counterpart (R3) | None client-side — documented gap per relink bar #2; render explicit-missing | measured-absence |
| CH-2 | Gallery portraits (14 Mita icons pathID 0; player 0 unset; players 1–9 share unresolved external pointer `file_id 2, path_id 276`) | Registry icons unset by the client (R5) | ART-layer portrait mapping; external pointer resolves with XC-3 dependency graph | derivable-later |
| CH-3 | `preview_prefab_key` load-call-site proof (`[unverified]` `'Personages/'` concat) | IL-stub bodies expose no Resources.Load site | XC-1 native pass | derivable-later |
| CH-4 | Outfit reflection targets — which Mitas reflect each outfit (COMP J7) | Code behaviour, bodies stripped | XC-1 | derivable-later |
| CH-5 | Trailing-decoration scene variants uncaptured by grammar T (`Location7_MitaCapRepeat`@level9, `Location15_MitaKind_Follow`@level17, `Location6_MitaKiller`@level8) | Compounds sit outside transform grammar T; ledgered, not dropped | Grammar extension or curation ruling at next J2 pass | derivable-later |
| CH-6 | Per-instance identity for unnamed classes (`MitaPerson` 93/45 containers, `MitaKiller` 31, `MitaFreak Enter` 17, `Mob_ChibiMita` 3) | Dumps carry no identity field (R4); counted, never attributed | Structural — counts reconcile exactly; only a deeper client parse could bind GOs→rows | measured-absence |
| CH-7 | Speaker-per-line attribution (J6 partial, R1) | Owned by DS-3 by fence; this dataset stores speaker NAMES only | See DLG-3/DLG-4 | derivable-later |
| CH-8 | Cartridge/achievement family membership for `mita-usual`/`mita-true` | Registry `nameSave` empty ×2 — no flash identity exists | None (registry fact); documented beside every join | measured-absence |
| CH-9 | Client evidence for 18 tier-4 wiki-only candidate names (16 evidence-less; Flower/Ballerina text-mention only) | Stub ladder forbids promotion without registry/loc evidence | Future content discovery; candidates ledger carries locators where they exist | derivable-later |

## achievements (DS-2 Part A)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| ACH-1 | Icon bytes for all 26 achievements (pathIDs 862–910; 0 hits in the 437-file `container-2d/resources.assets` export) | Sprites exist in-container but were outside the exported slice (AC-A5 PENDING) | Targeted AssetStudioMod re-export (art pass); Steam CDN URLs ride along as interim `icon.official_url` | derivable-later |
| ACH-2 | Unlock predicates 15/26 `unverified-behavior` (native-body grants: minigame controllers, set-completion counters) | Bodies stripped; 11 sites hard-serialized | XC-1 (owner-costed) or accepted-unverified with labeled gloss | owner-call |
| ACH-3 | `joins.minigame_id` resolved binds for tetro/racingfirst/logA/logB/hellwin/hellmegawin | Zero dumped award sites corpus-wide for those ids (DS-4 J3 null-target partials) | XC-1 or runtime capture; 4 other binds already attributed (3 hard + applesnake logic) | derivable-later |
| ACH-4 | `joins.chapter_attribution` (null ×26) | SPEC gap #1 (XC-2); wiki numbers stay `[community]` labels | XC-2 | derivable-later |
| ACH-5 | get-bool trust | Serialized `get=True` at indices {0,3} is editor-session pollution baked into prefab defaults (R-E1-2) | Permanent quarantine (`get_bool_trusted:false`) — no renderer may read it | measured-absence |
| ACH-6 | `registry_index == line_translate` stability ([inferred] append-only) | Holds on this build; patches may append | AC-A1 fail-fast keeps movement loud | measured-absence |
| ACH-7 | Fresh Steam global-% | Ephemeral plane captured 2026-08-25T02:19:10Z machine-plane | Live-capture cadence if ever charted | derivable-later |

## endings (DS-2 Part B)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| END-1 | Peaceful Mode real row (`mode-stub`, `state:"locked-stub"`) | Mode locked in this build (COMP J11 posture) | Patch rerun; stub cites `Menu.jsonl#line_index=130` + `dump.cs:206984` | derivable-later |
| END-2 | Safe-window percentages as proven data (17%/98% under `[community]`, third window has NO Basement_Safe component) | Numeric gates live in native safe-chain bodies | XC-1 | owner-call |
| END-3 | `safe-of-life` award chain (empty serialized chain, `unverified-behavior`) | Award rides native bodies | XC-1 | derivable-later |
| END-4 | Resolution of 3 dead-reference edges (serialized `m_Target` 0), incl. `CoreSkip.StopWait` whose type exists nowhere in il2cpp metadata | Destroyed-target calls in shipped scenes | None — ledgered residue, never resolved | measured-absence |
| END-5 | Trigger context for #6042/#1041 (`feeds_ending` = 0 by measurement) | No UnityEvent anywhere targets the hosts; triggers ride native bodies (#6042 `onStartZeroIndex=True`) | XC-1 | derivable-later |
| END-6 | Choices routed purely through code (no UnityEvent) | Edge set bounded by serialization; 371-node census is a floor | XC-1 + community cross-check continuation | derivable-later |

## dialogue (DS-3)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| DLG-1 | Entity slugs for 5 speaker themes (MitaKnow, MitaFon, White, Creepy, MitaDream) — `slug:null, pending-curation` | Brief/D6 fence: never guessed | Owner/research confirmation, one ruling each | owner-call |
| DLG-2 | Canonical alignment of the 9 provisional theme slugs with built DS-1 ids (theme "Mita" ↔ `mita-usual`, etc.) | Mapping predates B-1's emission (`provisional-pending-ds1`) | DS-1/DS-3 curation pass over `relinks/dialogue-speaker-theme--character.jsonl` | derivable-later |
| DLG-3 | Structured speaker on 107 nodes (D6 PARTIAL: 96.23% vs ≥99%) | choice_case/quest_box/pet_dialogue serialize no speaker field — structural ceiling | None possible client-side; 100% coverage within kinds that have a mechanism | measured-absence |
| DLG-4 | dialogue→audio join (`voice_present` null everywhere) | No serialized join exists; AudioDialogue is a separate carrier family linked at runtime | Carrier-family analysis or runtime capture | derivable-later |
| DLG-5 | Chapter field (null ×2839) | SPEC gap #1 (XC-2) | XC-2 | derivable-later |
| DLG-6 | 12 dangling `nextText` targets (1 hosts GameObject_Destroy, 11 host none) | Measured, ledgered with reasons in `_ledger/dangling-edges.jsonl` | None — explained-diff set | measured-absence |
| DLG-7 | 8 condition hints with no serializing target row (LD1 119 · LD14 75/139/163/180 · LD19 378 · LD7 271/655) | Explicitly ledgered in `build-meta.json.unattached_rows`; 320+8==328 invariant holds | None — explicit residue | measured-absence |
| DLG-8 | Branch-fork destinations as node refs (10 wired L14 slots text-keyed, `dst:null`) | All 10 target loc rows no component serializes; `carrier-for-index-not-found` is not dangling when in-range | None — data as-is | measured-absence |
| DLG-9 | EN `Location 3` line 12 U+FFFD (outside the 7 LD12 ledger rows) | Quest-label category, out of D4 scope | Loc-layer encoding ledger decision | derivable-later |
| DLG-10 | Spec §2.1 parity claim correction | Measurement REFUTED exact parity (4 locale tail deltas, ledgered as data) | Specifier's text amendment; data already correct | derivable-later |

## cartridges (DS-4)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| CAR-1 | Pickup carriers for `mtad2`, `mtacore` (`registered-unresolved-pickup`, `pickup_ref:null`) | No FlashTaker dump carries them; leads on file: `level20/Location18_Flash` has no save field; Core grant names itself in loc but no dump carries the call | Continued sweep / XC-1 / runtime | derivable-later |
| CAR-2 | `depicts_character_id` for cartridge `mta` | No C13 anchor — DS-1 registry nameSave empty for MitaUsual/MitaTrue | Curation ruling shared with SCN-3 | owner-call |
| CAR-3 | Scoring rules/thresholds (`scoring_derivable:false` ×17) | Bodies stripped; rule_evidence restricted to serialized counters + loc text | XC-1 (owner-costed toolchain) | owner-call |
| CAR-4 | Pumpkin-clicker→`outfit:HellVamp` upgrade from logic/partial to hard | Wiki-asserted; zero dumped ClothCompleted sites outside levels 5/6 | Dumped site or XC-1 | derivable-later |
| CAR-5 | Display-name table for prefab/carrier/tamagotchi rows (`name_loc:null`) | Client ships none (grep-proven) | None — pages compose `client_key` + cited `community_alias` | measured-absence |
| CAR-6 | Client surface for 4 wiki-only minigames (Fly Console, Forgotten Panels, Monster-Slap, Destroying Glitches) | Sweep found no class/loader/name evidence; "Hetoor"/"Spaceracer" grep zero hits | Tier-4 posture: no row/candidate until evidence exists | derivable-later |
| CAR-7 | Promotion decision for the `Metroidvania_*` cut-content family (tier-3 candidate; 48 byte-identical dumps) | Shipped-but-unused; held, never promoted | Owner interest, else stays candidate | owner-call |
| CAR-8 | Tamagotchi reachability (×4 `present_but_unreachable:true`) | Peaceful-Mode-adjacent lock (COMP J11) | Patch watch like XC-12 | derivable-later |
| CAR-9 | Arabic `MiniGame MakeManeken` tail (34 lines vs 35 elsewhere) | Sole locale skew, reproduced from files (AC-9) | Renders declared filler; re-derived per patch | measured-absence |

## documents (DS-5)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| DOC-1 | Readable note content (`text_mechanism:"unresolved"` ×160, `text_loc:null`) | Unity_Note serializes zero payload fields; no loc category; no scene Text payload (negative findings re-proven); texture hypothesis unproven | Chain: XC-4 sprite index → XC-3/P5 hierarchy → XC-1; until then notes render as placed interactables with wiring | derivable-later |
| DOC-2 | Sprite names behind raw `sprite_ptr` values (18 wired notes) | R5 index absent | XC-4 | derivable-later |
| DOC-3 | Book→parsed-scene bindings (`consumer_scene` is subtree-level only) | Same R5 index | XC-4 | derivable-later |
| DOC-4 | `chapter` column (null ×14) | P5 map (XC-2) | XC-2 | derivable-later |
| DOC-5 | Proof of script-grant mechanisms for profiles rows 6/9 (`mtad2`, `mtacore`) | Grant calls undumped; Core label verified (`CoreSoft.jsonl#line_index=37` "Get Flash Drive") | XC-1 | derivable-later |
| DOC-6 | Set-completion predicates (`ACHI_cartridgeplayers`/`ACHI_mitastory` counting logic) | Code body empty | XC-1 | derivable-later |
| DOC-7 | Novella actor identities (presentation ints/gradients only) | Spoken lines belong to DS-3 by boundary; actors carry presentation data | DS-3 personage curation (DLG-2) | derivable-later |
| DOC-8 | zh-Hans/Hant Location19 book pages (4/8 each) | Locales ship without them (whole zh subset 16 files) | Client artifact; cells derived from disk, filler renders | measured-absence |

## scenes (DS-6)

| ID | Missing | Why | Unblock | Class |
|---|---|---|---|---|
| SCN-1 | Marker rows (v0 `_meta`-only) | No-orphan rule absolute (XC-5) | Projection rerun post-DS-4/DS-5; monster/save-point owners first | derivable-later |
| SCN-2 | Coordinates for 76 `pptr-unresolved` POIs (FlashTaker hooks 19, MitaAIMovePoint 25, Trigger_DistanceCircle 18, Trigger_Teleport 14) | Transforms not in corpus | XC-3 S9 stage | derivable-later |
| SCN-3 | Curation ruling for `flashes:mta` (level17 pickup matches no gallery save_key) | Namespace divergence, `curation_status:"ruling-required"` (spec §9-R3) | Owner/research confirmation | owner-call |
| SCN-4 | Slug assignment for `mtad2`/`mtacore` curation rows | Mirror of CAR-1 | With CAR-1 resolution | derivable-later |
| SCN-5 | Fog-anomaly identity (`LightRenderer_Fog` ×15 kind `other`) | Name-coincidence until code analysis proves monster linkage (J6 logic-tier open) | XC-1 | derivable-later |
| SCN-6 | Next-tier POI enumeration (KeyHint ×382, MakeManeken dummies ~276, Trigger_Event ×334, ObjectInteractiveItemTake ×11, Transform_PositionCamera ×30, Transform_Magnet ×191, Rigidbody_StartVelocity ×27, MovePointsStartFinish ×7, MenuLocation ×16, MenuNextLocation ×52) | v0 emitted the measured priority classes; counts pinned, never dropped | Next emitter tier (986-row floor already exceeds spec §5's 650) | derivable-later |
| SCN-7 | Spawn-table prefab identity (`Event_CreateResource` cross-container refs `file_id>0`, `status:"unresolved-target"`) | Global pathID index absent | XC-3 | derivable-later |
| SCN-8 | Scene display names (`display_name_loc` null v1) + chapters for part-0 levels (15 non-zero pointers of 20 story levels) | SPEC gap #1; zero parts emit null, never guessed | XC-2 | derivable-later |
| SCN-9 | Objective pool for level20 (`LocationHint Location18` contentless everywhere; French ships a 0-byte shell) | Contentless ≠ missing (DS-3 §4); no pointers fabricated | None — classified, not alarming | measured-absence |
| SCN-10 | level18 `Scene_Load` | Measured absence; recorded as the lattice's ledger row | None | measured-absence |
| SCN-11 | level23 binding (role `unbound`: gameplay classes, no World/Scene_Load/location) | Identity unresolved — Peaceful stub vs cut/test level | Research/patch watch; full carrier inventory shipped | derivable-later |

## Closure documentation defects (found during assembly)

| ID | Defect | Where | Fix |
|---|---|---|---|
| DOCX-1 | Files bullet degenerates into hundreds of repeated `ObjectInteractive ×312` tokens (generator bug in the ledger prose; `poi.jsonl` data unaffected) | `extracted/data/scenes/README.md` line 15 | Repair the README generation at the next scenes emitter run |
| DOCX-2 | Position-truth census line disagrees with the emission: build log says inline 346 / none 564 (Transform_Position 71 inline, MitaAIMovePoint 31, Trigger_DistanceCircle 32 pptr); emitted `poi.jsonl` measures inline 298 (ObjectItem 262 + Player_Teleport 13 + Transform_Position 23) / pptr-unresolved 76 / none 612 — the scenes README already carries the correct census | `docs/research/build-log.mdx` B-6 block | Corrected by note in the CLOSURE-1 build-log block (log is append-only) |
| DOCX-3 | Staging duplication: canonical `extracted/relinks/` copies coexist with emitter-owned parked copies under `data/*/relinks/` | Both trees | Intentional until XC-6 lands — emitters regenerate their staging dirs; the canonical tree is the read surface (`relinks/_assembly-provenance.jsonl` records the policy) |

## Measured absences (not missing — proven so no piece re-chases them)

| ID | Fact | Evidence |
|---|---|---|
| MA-1 | `Location21_DialogueRandom`: zero instances across all 51 containers — router kind emits nothing | DS-3 D-build measurement (deviation 5) |
| MA-2 | French-only `LocationDialogue Location16` = 0 bytes → `contentless` for fr, filler elsewhere | availability.csv; RAW tree |
| MA-3 | Console-game choice conditions: none exist in `choice_nodes.jsonl` (J6 meta-only file IS the answer) | DS-4 J6 measured absence |
| MA-4 | ComicBook is a post-processing effect, not readable content (21 containers, 1/scene) | DS-5 negative finding 1 |
| MA-5 | No loc category carries note/paper/profile text; `Translation.jsonl` = 1 record `"-"` | DS-5 negative finding 2 (English 65 categories) |
| MA-6 | Only 49 >60-char `m_Text` literals corpus-wide, all dev/UI strings; zero TextMeshPro | DS-5 negative finding 3 |
| MA-7 | Second profile registry: none (MenuPersonage single instance; class/literal censuses close) | DS-5 R2 adjudication executed |
| MA-8 | `feeds_ending` direct edges: 0 (trigger context rides native bodies) | endings emit-ledger feeds-ending-rule |
