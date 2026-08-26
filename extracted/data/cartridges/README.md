# extracted/data/cartridges/ — honesty ledger & regeneration notes

Built 2026-08-25 by builder **B-4** against the arbiter-approved spec
[`docs/specs/dataset-cartridges.mdx`](../../../docs/specs/dataset-cartridges.mdx)
([ds456-arbiter](../../../docs/research/verifications/ds456-arbiter.mdx): DS-4
APPROVED). Corpus pins: **buildId 19029065**, **version_label 0.93L** on every
record (read from `extracted/EXTRACTION-LOG.md` `pipeline-defaults`).

## Files

```
cartridges.jsonl                        # _meta + 23 cartridge_item rows (spec §4.1)
minigames.jsonl                         # _meta + 17 minigame rows   (spec §4.2)
cartridges-minigames.candidates.jsonl   # stub ladder tier 3 only    (spec §7)
relinks/cartridge--character.jsonl      # J1 mirror of C13 anchors, dual typed edges
relinks/cartridge--scene-placement.jsonl# J2 meta-only (parked until scenes dataset)
relinks/minigame--achievement.jsonl     # J3 award-site ∪ type-tag edges
relinks/minigame--scene-carrier.jsonl   # J4 carrier classes × containers + dedupe record
relinks/minigame--outfit-unlock.jsonl   # J5 ClothCompleted chain
relinks/minigame--choice-condition.jsonl# J6 meta-only (measured absence)
build/emit_cartridges.py                # deterministic emitter (this tree's regen)
```

Regeneration: `python extracted/data/cartridges/build/emit_cartridges.py`
from the repo root. Every number is re-measured from the §2 artifacts at run
time; nothing is copied from prose. Byte-determinism proven: two consecutive
runs reproduced all nine JSONLs md5-identical.

## Pins carried in `_meta` headers

- **TelevisionGames −1 name offset (binding).** C5 entries carry
  `indexStringNameGame` 1 (`Fight`) and 2 (`Pinguin`) while the category spans
  lines 0–1. Chosen: `GetString("TelevisionGames", indexStringNameGame − 1)`
  → Fight = line 0 `"Dairy Scandal"`, Pinguin = line 1 `"Penguin Piles"`.
  Rejected identity offset, with its failure: it would name the fight-styled
  entry "Penguin Piles" and the penguin-styled entry "Dairy Scandal" —
  rejected on semantics exactly like DS-1's clothes off-by-one. Both
  computations recompute cleanly in all 34 locale dirs (AC-4).
- **Boilerplate dedupe (R4).** All 48 `MinigamesController.txt` dumps hash
  into exactly 4 content groups sized **19/16/12/1**; `level2`'s hash is
  shared by all 12 members of its group (no dump and no group is privileged).
  Identical hashes collapse to one logical instance; no carrier count counts a
  duplicate-hash dump twice.
- **Dependency auto-load dedupe.** `CarSpace_*` / `MakeManeken_*` prefabs list
  in 48 of 51 asset-lists via AssetStudioMod dependency auto-load; their
  `carrier_containers` collapse to canonical prefab home (`resources.assets`)
  plus loader container.
- **Slug rule.** `cartridge_id` = save_key lowercased with hyphens inserted at
  every letter↔digit boundary (`mtacap → mta-cap`, `plr1099 → plr-1099`);
  additive only — `save_key` stays the primary client identifier.

## Namespace honesty (AC-3)

C1/C2 carry key `mta`, but DS-1's registry leaves `nameSave` **empty** for
`MitaUsual`/`MitaTrue` (DS1-CONTRACT nullability note), so no C13
`flashes:mta` anchor exists. The `mta` row therefore carries
`depicts_character_id: null` with the fact named in its `missing_fields`.
Joins ride C13 anchors verbatim — never an assumed `nameSave` equality.

Measured corroboration recorded in the J1 `_meta`: all 23 registry keys are
wired one-to-one as `MenuPersonage.OpenPersonage("<save_key>")` call sites
across 23 `level2` dumps (e.g. `ButtonMouseClick_#2179.txt` → `"mtad2"`),
confirming the gallery IS the cartridge album.

## Completeness register (what stays unresolved today)

| # | Risk | State in this build |
|---|---|---|
| R1 | DEC files are IL-stubs (fields/signatures only) | `scoring_derivable: false` on all 17 minigame rows; `rule_evidence` restricted to serialized counters + loc text; unblock ledgered: native-code decompile pass over `GameAssembly.dll` (owner-costed toolchain row) |
| R2 | TV −1 offset is a pinned hypothesis | pin + both recomputations above; AC-4 makes any verifier redo them |
| R3 | `mtad2` / `mtacore` pickups | tier-2 rows, `pickup_ref: null`; leads on file: `level20/Location18_Flash.txt` serializes only a `novella` PPtr (no `save` field); the Core-computer button names itself in loc (`CoreSoft.jsonl#line_index=37` "Get Flash Drive") but no dump carries the call |
| R4 | Template-dump boilerplate | partition asserted mechanically (above) |
| R5 | Container ≠ chapter | rows store measured containers only; `container_location_binding` is `[inferred]` via DS-3 §3.6; chapter attribution belongs to the scenes dataset |
| R6 | Peaceful Mode additions | tamagotchi-activity rows flagged `present_but_unreachable: true`; buildId-stamped rerun diffs the set |
| R7 | Post-0.93L silent builds unknown | buildId stamps on every record; rerun diff is the only instrument pre-harvest |
| R8 | No client display-name table for prefab/carrier minigames | `name_loc: null` honest (only TV rows resolve through `TelevisionGames`); `community_alias` cited, never a key |

## Wiki-only minigame claims (tier 4 — no row, no candidate)

Per spec §7 item 4 these get no row and no candidate; noted here against the
research citation ([game-research §4](../../../docs/research/game-research.mdx)
— Fandom Minigames tabulation):

- **Fly Console** ("don't move for 2 minutes", "collect 25 coins") — no client
  surface found in the sweep; its numbers exist nowhere in the client.
- **Forgotten Panels** — no matching class/loader/name evidence found.
- **Monster-Slap** — no matching class/loader/name evidence found.
- **Destroying Glitches** ("4 phases") — no matching class evidence found.
- The community names "Hetoor"/"Spaceracer" grep **zero** hits across
  `stringliteral.json` and every locale's four minigame categories — they
  appear only as cited `community_alias` values, never as keys (AC-8).

## Locale availability (derives, never hardcodes)

Page-facing availability computes from the presence of the four categories
(`MiniGame CarSpace`, `MiniGame MakeManeken`, `MiniGame Shooter`,
`TelevisionGames`) in each of the 34 locale dirs, reconciled against
`localization/_ledger/locale-delta.jsonl`. Measured skew: `MiniGame
MakeManeken` has **34 lines in Arabic and 35 in the other 33 locales** — the
sole cell skew; the Arabic cell renders the declared explicit-filler state.
Self-check AC-9 deletes the Arabic file in a scratch copy and watches the
computed cell flip.

## Emit-stage registration fence

Relink files park under `relinks/` and move to `extracted/relinks/` when the
emit stage registers in the PIPE manifest. Per the ds456-arbiter agenda-1
ruling, that registration lands **in the same commit** as the DS-4 §1
restatement to the 11-row-overlap scope (the mita-side pairs DS-5 consumes by
reference; the 10 player-side pickups are this dataset's alone), before
either emit stage runs.
