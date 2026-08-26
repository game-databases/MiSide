# scenes — dataset honesty ledger (DS-6)

Emitted by `build/emit_scenes.py` (builder B-6, 2026-08-25) against
[docs/specs/dataset-scenes.mdx](../../../docs/specs/dataset-scenes.mdx)
(post-F-DS6; verifier [ds6-vA](../../../docs/research/verifications/ds6-vA.mdx)
PASS). Build **19029065** / **0.93L**. Regenerate:
`python extracted/data/scenes/build/emit_scenes.py` (set `MISIDE_HARVEST_ROOT`
when extracted/harvest/ lives elsewhere) — reruns are byte-identical (no
wall-clock inputs; floats carried verbatim from the MB dumps).

## Files

- `scenes.jsonl` — 24 registry rows (20 story + boot/title/menu + level23 `unbound`).
- `scene-links.jsonl` — 57 rows: 19 loads / 7 unloads / 15 continues edges, 15 chapter pointers, 1 level18 absence ledger row.
- `poi.jsonl` — 986 placement-bearing instances: ObjectInteractive ×312, ObjectItem ×262, Transform_Position ×71, MinigamesController ×70, Trigger_DistanceCircle ×32, MitaAIMovePoint ×31, Location10_MitaInShadow ×28, Event_CreateResource ×24, FlashTaker ×21, Mob_Maneken ×20, Scene_Load ×19, Mob_Cockroach ×16, LightRenderer_Fog ×15, MitaKiller ×15, Trigger_Teleport ×14, Player_Teleport ×13, MitaFreak Enter ×8, Shooter_Enemy ×4, Mob_ChibiMita ×3, TamagotchiGame_Cartridge_Cartridge ×3, Basement_Safe ×2, QuadLiner_Enemy ×2, TamagotchiGame_Cartridge ×1.
- `spawn-tables.jsonl` — 24 Event_CreateResource rows.
- `markers.jsonl` — M0 projection rerun: 70 entity-backed rows (21 cartridge via DS-4 save_key · 11 profile_document from DS-5 placement · 38 minigame_access carrier pairs, the latter two families scene-granular with `poi_id:null`); family ledger + S9 dispositions in `_meta`.
- `poi-kinds.json` — curated class→kind rulings.
- `relinks/` — inverted indexes parked until stage registration (B-1 precedent).

## Position truth census

inline 298 · pptr-unresolved 76 · none 612.
`world-assumed` appears ONLY on World.positionSpawn (scenes.jsonl).
Player_Teleport carries inline floats but its frame is unproven (IL-stub
bodies) → `space:"unknown"`. Transform_Position sets are parent-relative
where `myParent ≠ 0`, else `unknown`; S9 calibration will refine both.
ObjectItem face/hand offsets are `object-local-offset` and excluded from
marker projection. The transform stage (PIPE S9) flips pptr-unresolved rows
to inline without schema change.

## Measured corrections to the spec (dumps stay the anchor)

1. **level7 unloads** `"Scene 5 - StartHorror"` — DS-6 §2.3's table shows
   `—`; `mb-dump/level7/Scene_Load.txt` measures the string verbatim. Rows
   follow the dump.
2. **Non-zero chapter pointers = 15**, not §5's projected 16.
3. **Event_CreateResource distribution**: levels 3–19 and 21 carry them;
   multiples at 4/5/6 (×2) and 17 (×3); absent from 20 and 22 — §2.7's
   "one per story level ± extra in 4/16/17" was a gloss.
4. **eventDay is holiday-gated**: measured values are only
   halloween (0, ×3) and christmas (1, ×21); DEC enum adds `none` (2,
   unused). "Day-gated" reading corrected.
5. **LocationHint pools: 18 in English, not §5's 19** — and
   `LocationHint Location18` (level20's objective pool) is CONTENTLESS in
   every locale: French ships a 0-byte file, no other locale ships any
   (measured census). Classified per DS3 §4: contentless ≠ missing; no
   pointers are fabricated for level20.
6. Some Transform_Position instances serialize an EMPTY positions array →
   labelled source "none", never inline-with-zero-points.

## Curation rulings

- `flashes:mta` (level17 FlashTaker) matches no DS-1 gallery save_key →
  relink row `curation_status:"ruling-required"` (spec §9-R3); display facts
  ship, no slug invented.
- `mtad2` / `mtacore` ride no FlashTaker (console grant / none) →
  `registered-unresolved-pickup` rows mirroring DS-4's tier ladder.
- `LightRenderer_Fog` ×15 stays kind `other` with
  `fog-anomaly-candidate-unproven` — J6's identity question is open.
- TamagotchiGame pet cartridges (level3, ×4) are the distinct in-fiction
  kind (AC S5), never merged with flash drives.

## Deferred families (enumerated next tier — never dropped)

Interface_KeyHint_Key ×382 and the MakeManeken_Interaction dummy family
(~276 corpus-wide) are measured but not emitted as POI rows this pass
(UI-hint/dummy carriers; counts pinned here and in poi-kinds.json).
Trigger_Event ×334 (level scenes), ObjectInteractiveItemTake ×11,
Transform_PositionCamera ×30, Transform_Magnet ×191,
Rigidbody_StartVelocity ×27, Transform_MovePointsStartFinish ×7 likewise
await their tier; endings' choice-node dataset already consumes part of
Trigger_Event/ObjectInteractive evidence. Menu-side pickers (MenuLocation
×16, MenuNextLocation ×52) live in level2 and stay out of the physical
carrier set.

## Markers v1 — M0 projection rerun (map-viewer §3)

The no-orphan rule (spec §3.5) still governs: markers exist only for
entities an owning dataset's emitted file confirms. DS-4 (cartridges), DS-5
(profile documents) and the minigame--scene-carrier relink have landed, so
the rerun emits:

- **21 `cartridge` rows** — FlashTaker poi rows joined through
  `joins.save_key` to DS-4 `cartridge_id`s (join audited: exactly one DS-4
  row per save_key, pickup_ref.container equal to the poi container).
  19 carry their pptr target with `status:"awaiting-transform-stage"`; the 2
  whose `objectTake` is null serialize no transform at all and stay
  `scene-granular` — never a faked spot.
- **11 `profile_document` rows** — placement-sourced shape
  (`placement_source:"DS-5"`, `poi_id:null`, scalar `container` split
  emitter-side out of any compound id, DS-5 `placement` verbatim,
  `instance_census`). Scene-granular always: DS-5 names the carrier
  component, not a resolved transform.
- **38 `minigame_access` rows** — placement-sourced carrier pairs
  (`minigame_id` × `container`) over the 22 covered
  containers, edge `mechanism/status/method` verbatim;
  `instance_census.minigames_hosted` keeps multi-minigame containers from
  reading as one-of-N (level9 hosts 4 minigames over 3 controllers).
  Per-instance controller anchoring is prohibited (A-MV1 OQ-7).

Deferred families stay deferred with reason codes in `_meta`
(`pending_families[]`, Σ poi_rows = 709 eligible rows):
tamagotchi pet cartridges ×4 (`owner-ruling-pending`), save points ×19 +
unowned teleports ×27 (`no-entity-dataset`), move points ×102,
spawn events ×24 (`unresolved-target-until-xc3`), safes ×2, interactables
×344 (`scn6-tier-2`), monsters ×96, and level1's 3 controllers
(`no-carrier-edge`). Confirmed-but-unplaced entities (`mtad-2`, `mtacore`,
plus the 3 placement-less profiles under their DS-5-declared
`script_granted`/`story_granted` vocabulary) are accounted in
`_meta.unplaced` — no container inference from `[inferred]` bindings.

The 76 pptr-unresolved positions all defer as
`deferred:s9-not-run` (`_meta.position_dispositions`): PIPE S9's
scene-transform walk is the coordinate unblock and has not run. Registry v2
(display_label_loc, per-kind counts, artwork-driven status) is written by
the site artifact step additively over v1 fields.

## Non-story levels (evidence classes, Principle zero)

level0 boot: SceneStart, LogoPresent ×24(corpus), ComicBook. level1 title:
SceneLoading_Preloading, ChangeLanguageStart, OptionsGame. level2 menu:
MenuPersonage, MenuLocation ×16, MenuNextLocation ×52, MenuChangeLoadLevel.
level23 `unbound`: MitaKiller, Shooter_Enemy ×4, Achievement_function,
win-animation tracks; no World, no Scene_Load, binds no location (§9-R5).
