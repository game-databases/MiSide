# Documents & lore collectibles — dataset (DS-5 build B-5)

Contract: [`contracts/dataset-documents.mdx`](../../../contracts/dataset-documents.mdx)
· Spec: [`docs/specs/dataset-documents.mdx`](../../../docs/specs/dataset-documents.mdx)
(arbiter-approved, [ds456-arbiter](../../../docs/research/verifications/ds456-arbiter.mdx))
· Build pins: buildId **19029065**, version **0.93L** (EXTRACTION-LOG
pipeline-defaults == census/detect.json verified at emit; stale-log refusal armed).

| File | Rows |
|---|---|
| `profile_documents.jsonl` | 14 (11 placed · 2 script-granted · 1 story-granted) |
| `world_documents.jsonl` | 166 (160 notes + 5 paper parts + 1 novella surface) |
| `books.jsonl` | 8 localized readable-book textures |
| `relinks/document--character.jsonl` | 28 edges (fwd+inv) |
| `relinks/document--achievement.jsonl` | 28 edges (fwd+inv) |
| `relinks/document--scene-membership.jsonl` | 354 edges (fwd+inv) |
| `relinks/document--event-wiring.jsonl` | 370 edges (fwd+inv) |
| `relinks/document--minigame.jsonl` | 12 edges (fwd+inv, incl. magnet census edge) |

Relinks are PARKED here (write scope) and move to `extracted/relinks/` at the
PIPE emit-stage registration commit — DS-1 relocation precedent
(`extracted/data/characters/README.md`).

## Honesty ledger feed (missingdata.md input; spec §8 AC-10)

- **Note content carriers unresolved (R1)** — all 160 `note` rows carry
  `text_mechanism: "unresolved"`, `text_loc: null`. The component serializes
  zero fields ([Unity_Note.cs](../../../extracted/decompiled/main/Assembly-CSharp/Unity_Note.cs));
  no loc category, no scene Text payload (negative findings below); the
  baked-texture hypothesis stays unproven until the R5 sprite index exists.
  Notes render as placed interactables with their serialized event wiring —
  never with invented prose.
- **Script-granted profiles** — `mita-2-d` (row 6, `mtad2`) and `mita-core`
  (row 9, `mtacore`) carry `placement: null`,
  `placement_mechanism: "script_granted"`. Evidence: `CoreSoft.jsonl#line_index=37`
  = "Get Flash Drive" for the Core computer grant (row 9);
  `level2/ButtonMouseClick_#2179.txt` passing `"mtad2"` (DS-4 §3.1 finding 4)
  for row 6.
- **Story-granted profile** — `mita-true` (row 13) is keyless in BOTH
  namespaces (registry `nameSave` empty; no FlashTaker anywhere):
  `flash_save_key: null`, `name_is_shared: true` (Menu line 83 reused with
  row 0).
- **`chapter` is null on all 14 rows** (R3) — fills only from the P5
  level↔chapter map; community chapter attributions never enter rows.
- **R5 raw-pointer state** — `sprite_ptr` values are raw `{file_id, path_id}`
  PPtrs; naming waits on the sprite-pathID→export-name index (72,115 exported
  sprites). `books.jsonl` scene bindings stay at subtree-name level
  (`consumer_scene`), never asserted to a parsed scene.

## Placement authority (consume-by-reference)

Per [DS-4 §1](../../../docs/specs/dataset-cartridges.mdx) shared-source ruling,
this dataset is NOT a placement authority: the 11 placed rows'
`(save_key, container)` pairs consume **by reference** to DS-4 AC-2's pickup
census (11-row Mita-side subset; the 10 player-side pickups are DS-4's alone).
Emit-time state: ds4-emission:extracted/data/cartridges/cartridges.jsonl.
Reconciliation against `cartridges.jsonl` is wired into
`selfcheck_documents.py` and runs mechanically whenever that emission exists;
divergence settles toward DS-4's census, never a silent second derivation.

## Negative findings re-proven this pass (spec §8 AC-5)

1. **ComicBook is not readable content** — the only `ComicBook` class is a
   Colorful post-processing image effect
   ([Colorful/ComicBook.cs](../../../extracted/decompiled/main/Assembly-CSharp/Colorful/ComicBook.cs));
   dumps re-counted this pass: exactly one per scene file in **21 containers**.
2. **No loc category carries note/paper/profile text** — English ships **65**
   categories; none matches notes/documents/profiles; `Translation.jsonl`
   holds exactly **1 record, `"-"`**. Re-walked x34 at emit: `Personages` =
   26 records in every locale.
3. **In-scene `Text` payloads are not documents** — re-scan of all 18,117
   `Text*` dumps found exactly **49** `m_Text` literals longer than 60 chars,
   all dev/UI strings. Zero TextMeshPro components exist in any dump.

## R2 unification adjudication — executed, not assumed (spec §8 AC-6)

Searched for a second profile registry: (a) `MenuPersonage` typed dumps across
all 51 containers — exactly ONE instance (`level2/MenuPersonage.txt`);
(b) decompiled Assembly-CSharp classes touching `nameSave` /
`indexDescriptionStringFile` / `resourceMita` — only `Menu`, `MenuPersonage`,
`PersonageResource`; (c) all `*Personage*` / `*Profile*` classes —
`Location18_Personage` (novella actor presentation), `Menu_CasePersonage`
(UI button), `MenuPersonage`, `PersonageResource`; (d) il2cpp string literals —
`/Save/Flashes` is the only flash collection path. **Outcome: no second
serialized profile registry found; unification stands.** Falsifier, verbatim
from spec §2.2: if the P5 scene parse or a future native decompile surfaces a second serialized profile registry (a profile screen object, a second save-key family), the emit pass forks `profile_document` away from cartridge identity and ledger both shapes - never silently merge

## Measured divergences found while building (finer measurement, no contradiction)

1. **Book art parity is NOT total x34.** Spec §2.3 recorded "8/8 x34";
   re-walking `art/localization-art/*/Textures/` this pass measures **32 x 8/8**
   and **ChineseSimplified + ChineseTraditional 4/8** — both zh locales lack
   the four `Textures/Location19/Book {1,2,3,4}.webp` pages entirely (their
   whole localized subset is 16 files). `books.jsonl` derives availability
   from the filesystem (never asserts), so the cells already say this; the zh
   cells render the declared explicit-filler state for those four pages.
2. **Novella AudioSources: 8, not the 7 sketched in spec §2.4** — serialized
   refs `audioMain, audio1..audio5, audioNext, audioReady` (stored verbatim in
   the row's `audio_source_refs`).
3. **Non-level note copies group by content hash into groups sized
   [25, 25, 25, 23]** across 25 non-level containers; under the pinned §7-R4
   field-signature rule they are **1 shared-prefab group** (Unity_Note
   serializes no payload field beyond the MonoBehaviour base, so every copy's
   signature is empty). Both numbers live in `world_documents.jsonl`
   `_meta.dedupe`.

## Interpretation decisions (documented deviations, no spec violations)

1. **`subject_character_id` uses the BUILT DS-1 slugs** (e.g. `mita-usual`,
   `mita-short-hairs`) — spec §3's draft column predates B-1's emission; J2
   names the built emission the join authority. Multiset equality per AC-1 is
   on `(resource_path, lore_line, name_line)`, which matches the registry
   byte-for-byte.
2. **`carrier.path_id` = TRUE serialized component PathID** resolved by the
   B-3-method raw-header identity pass (AssetStudioMod `_#N` dump suffixes are
   tool ordinals, not PathIDs — build-log B-3 finding 1). Dump filenames ride
   along as `carrier.dump_file` so every row greps clean to its evidence;
   `scene_ref.gameobject_path_id` is verbatim from the dump text.
3. **Row 0 `flash_save_key` = `"mta"`** — the measured FlashTaker namespace
   value; the registry's empty `nameSave` fact stands documented right beside
   it (AC-1 single divergence).
4. **`event_wiring` row shape** — `{trigger, method, target_type, target_ptr}`;
   the spec triple `{method, target_type, target_method}` maps onto it:
   `method` = serialized `m_MethodName` (the target method),
   `target_type` = serialized assembly type short name; `trigger` adds the
   owning serialized field (`Events_Data._event[i]`,
   `Time_Events.EventsOnTime[j]@<time>`, `Button.onClick`,
   `pauseStart`/`pauseStop`).
5. **`scr_main` additive field** on paper-part rows — the serialized scrMain
   PPtr is J6's join payload; keeping it on the row makes the relink edge
   reproducible without re-opening the dump.
6. **Emitter/checker parked at `data/documents/build/`** — register in the
   PIPE stage tree at adoption, ordered after DS-4's stage per arbiter fence
   (recorded in the build-log handoff).
7. **Relinks parked in `relinks/` subdir** — move to `extracted/relinks/` in
   the registration commit (handoff below).

## Regeneration

```
python extracted/data/documents/build/emit_documents.py      # emit (stale-log guarded)
python extracted/data/documents/build/selfcheck_documents.py # AC scoreboard + rerun diff
```

Two consecutive emits are byte-identical (AC-9); the selfcheck proves it by
re-emitting into a temp dir and diffing bytes.

The book-art walk resolves `extracted/art/localization-art/` first; if that
subtree is triaged off the corpus drive, the emitter follows
`extracted/art/MOVED-TO.txt` mechanically (2026-08-25 C:-disk-full triage
relocated it to `D:\unpacked_game_data\MiSide\art-export\`).
