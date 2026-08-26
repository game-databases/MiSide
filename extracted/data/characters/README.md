# characters/ — DS-1 dataset (Mitas & Players)

Contract: [`contracts/dataset-characters.mdx`](../../../contracts/dataset-characters.mdx) ·
Spec: [`docs/specs/dataset-characters.mdx`](../../../docs/specs/dataset-characters.mdx)
(arbiter-approved, [ds123-arbiter](../../../docs/research/verifications/ds123-arbiter.mdx)) ·
Build: **19029065 / 0.93L** (pins read from
[`extracted/EXTRACTION-LOG.md`](../EXTRACTION-LOG.md) `pipeline-defaults`).

The character registry is data-driven and survives verbatim in
`harvest/mb-dump/level2/MenuPersonage.txt`: `resourceMita` size 14 +
`resourcePlayer` size 10 = **24 owned rows**. Display text is joined by
loc pointers (`{category, line_index}` through
`GlobalLanguage.GetString`, proven E1 step 7) — never copied per-locale;
per-entity locale availability derives from the four categories' presence
per locale dir (all 34 today), matching
`localization/_ledger/locale-delta.jsonl`.

## Files

| File | Content |
|---|---|
| `personages.jsonl` | `_meta` header line + exactly 24 data rows |
| `characters.candidates.jsonl` | `_meta` + stub-ladder tier 3/4 candidates (26 rows; tier 2 `loc_only` is EMPTY — registry desc indices consume Personages lines 1–14 exactly) |
| `relinks/character--scene-membership.jsonl` | J2 edges + unnamed instance census |
| `relinks/character--outfit.jsonl` | J3 outfit-table inventory + Clothes-line pin |
| `relinks/character--achievement.jsonl` | J4 collectible-family rows (22 keys) |
| `relinks/character--cartridge.jsonl` | J5 save identities (22 keys) |
| `relinks/character--dialogue-speaker.jsonl` | J6 speaker names + carrier keys |

**Relocation:** the five `relinks/*` files are parked inside this subtree
because this build pass's write scope excluded `extracted/relinks/`; move
them to `extracted/relinks/` when the emit stage registers in `run_all`
(same commit as the PIPE tree update, per arbiter residue item (a)).

## Schema superset vs spec §4.2

Two S2 fields absent from the spec's field table are kept as columns rather
than dropped — spec AC-3 requires every `PersonageResource` field to survive
as a column or an explicit drop-with-reason:

- `case_back` / `button_menu` — `{container, file_id, path_id}` or null
  (pathID 0); hard PPtrs into `level2` (gallery case art, menu buttons).
- Pointer objects carry `file_id`: a nonzero `file_id` means an
  external-dependency pointer whose target container is not yet resolved
  (AssetStudioMod dependency auto-load, E1 deviation 6); `container` then
  names the owning dump only. Today this affects one value class: the shared
  player gallery icon (`file_id 2, path_id 276`).

`character_id` derivation (additive only): mita rows = kebab-case of
`resource_path` (camel/digit boundaries split, lowercased); player rows =
`player-{gallery_order+1}` because nine of ten players have an empty
`resource_path` (spec's own example `player-3`). Rule order pinned so reruns
are byte-stable (`Mita2D` → emitted as `mita-2-d`).

## Honesty ledger (missingdata.md feed)

- **Version-category gap (R3).** 44 `Localization_UIText` components with
  `NameFile = "Version"` exist across the dumped containers (sharedassets3–23
  among them, plus level scenes and globalgamemanagers; counted this pass by
  grep over `harvest/mb-dump/`), but no `Version.txt` ships in any of the 34
  locale dirs — the version-sign text is unreachable via the loc layer.
  Documented gap per relink bar #2; never worked around.
- **Gallery icons unset (R5).** All 14 Mita `icon` PPtrs are pathID 0 →
  `gallery_icon: null`; player row 0 likewise. Player rows 1–9 share one
  icon pointer (external `file_id 2, path_id 276`, target container
  unresolved). Portraits belong to the ART layer; nothing here backfills them.
- **Empty save keys.** `mita-usual` (MitaUsual) and `mita-true` (MitaTrue)
  have `nameSave = ""` — no FlashTaker save identity; they appear in no
  cartridge/achievement family row (recorded in the cartridge file meta).
- **Clothes-line pin (R2).** Chosen: `GetString("Clothes", stringName − 1)`
  → Default/School/Vampire/Christmas for original/FIIdClSchool/HellVamp/
  Chirfns. Rejected: direct `GetString("Clothes", stringName)` — stringName
  13 falls outside every locale's Clothes category (13 records, indices
  0–12), and it renders `original` as "School". Both offsets recomputed from
  S8+S9 across all 34 locales this pass; pin recorded in the outfit file meta.
- **Uncaptured decorative scene variants.** Location-prefixed compounds with
  TRAILING decorations sit outside transform grammar T and are claimed by no
  edge (evidence FOR registered rows, ledgered not dropped):
  `Location7_MitaCapRepeat`@level9, `Location15_MitaKind_Follow`@level17,
  `Location6_MitaKiller`@level8.
- **Scene-instance identity (R4).** Unnamed instance classes
  (`MitaPerson` 93 instances / 45 containers, `MitaKiller` 31/31,
  `MitaFreak Enter` 17/17, `Mob_ChibiMita` 3/3) are counted per container,
  never attributed; counts equal the full suffixed mb-dump filename census
  exactly.
- **Speaker attribution (R1).** `character--dialogue-speaker.jsonl` stores
  speaker NAMES (Names lines 0–2) and carrier keys only — zero per-line
  attributions; that proof belongs to the dialogue dataset (DS-3).
- **Wiki-only names (tier 4).** None of Prankster / Long-legged / Mitaphone /
  Lower Half / Giant / Braided-Hair / Railway Chibi / Cool / Pretty /
  Wandering / Flower / Ballerina / Limping Person appears in
  `personages.jsonl`; each lives only in the candidates ledger with client
  locators or `evidence: []`. Wiki "Dummy Mita" maps to registered row 12
  (`MitaManeken`) and is therefore NOT a candidate.

## Regeneration

Outputs are byte-deterministic (fixed key order, sorted edges, stable
float repr); reruns diff clean. This pass ran as a manual curation pass by
builder B-1; the `run_all` emit stage that owns these files permanently is
registered later per spec §9 — its stage module reads the same sources
(§2 S1–S15) and must keep the schema doc
[`contracts/dataset-characters.mdx`](../../../contracts/dataset-characters.mdx)
in sync.
