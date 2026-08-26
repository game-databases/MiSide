# PROOF — MiSide extraction (P1 raw layer)

Completeness is PROVEN, not claimed. Every number below carries its
measurement method. Totals reconcile to the S2 census byte-for-byte;
`run_all` regenerates this file deterministically.

| Pin | Value |
|---|---|
| buildId | 19029065 |
| version label | VERSION 0.93L |
| Unity | 2021.3.35f1 |
| metadata version | 29 |
| scripting backend | il2cpp |

## 1. Source inventory

| Source | Count | Bytes | Measured how |
|---|---:|---:|---|
| SerializedFile containers | 51 | 583027900 | filesystem walk of `MiSideFull_Data` top level; name-family classification (`detect` stage) |
| Stream siblings (.resS/.resource) | 69 | 1694288048 | filesystem walk of `MiSideFull_Data` top level; name-family classification (`detect` stage) |
| **Container corpus grand total** | 120 files | 2277315948 B | sum of the two rows above |
| Localization tree (`Data\Languages`) | 3002 files / 2210 txt / 777 png + 3 psd | 371861650 | filesystem walk of `Data\Languages` (`census` stage) |
| Audio (`.ogg` family et al.) | 28727 | 1441448548 | filesystem walk of the game root (single recursive pass, `art-export` stage) |
| Video | 0 | 0 | filesystem walk of the game root (single recursive pass, `art-export` stage) |
| GI Enlighten tree (`MiSideFull_Data\GI`) | 62 | 5988963 | filesystem walk of the game root (single recursive pass, `art-export` stage) |
| Loose character templates (`Data\Custom`) | 17 | 11186378 | filesystem walk of the game root (single recursive pass, `art-export` stage) |
| Voice Editor `*_Data` (second content source, P7) | 118 | 37918664 | filesystem walk of `Miside Voice Editor_Data` |

Voice Editor extension mix: (none)=4, .assets=2, .config=1, .dll=106, .info=1, .json=2, .resource=1, .ress=1.
Full media families incl. per-locale art subsets: `MEDIA-CATALOGUE.md`
+ `media-catalogue.jsonl` (253 rows).

## 2. Coverage reconciliation

- Container sweep: attempted **51**, succeeded **51**, failed **none**.
- Bytes reconciled: succeeded 583027900 + failed 0 = census serialized 583027900 B ✔
- Attribution caveat: AssetStudioModCLI auto-resolves dependencies when dumping (E1 deviation 6), so per-source attribution reads each attempt's `loaded` list in `census/sweep-attempts.jsonl`, not naive per-file math.
- Localization: category files parsed + ledgered non-UTF-8 anomalies (2210 + 0) reconcile to the walked `.txt` total (2210) ✔
- Media catalogue rows reconcile to an independent re-walk of the game root (`art-export` FAIL-FASTs on any disagreement).

## 3. Residue ledger

- **levelN dump depth** [R-E1-1] — Level/scene dumps were measured first (sweep-budget.json) and swept with the rest; dialogue/location/endings component coverage inside levelN dumps still needs a curation-pass read before claiming depth.
- **achievement unlock-state ambiguity** [R-E1-2] — DataAchievements `get` bools serialize unlock state into assets; defaults vs live state must be separated downstream (entity-curation).
- **locale category/texture skew** [R-E1-3] — Per-locale category sets differ (64-76 on buildId 19029065) and texture subsets differ (JA 20 png vs EN/RU/FR 26); skew is ledgered in localization/_ledger/locale-delta.jsonl instead of asserted uniform.
- **GI cache level3-only** [R-E1-4] — Enlighten Global-Illumination precomputed data exists only for level3; catalogued in MEDIA-CATALOGUE, never chased.
- **cyclic typetree tails unexpanded** [I-S4] — AssetStudioModCLI 0.19.0.1 (cycle guard on upstream 6b66ec7) stops expanding a recursive serializable type at re-entry: inside affected dev-console components (ConsoleEditor_HierarchyCase family, dump.cs:99328) the cyclic field's nested tail is not expanded — bounded loss confined to dev-console scaffolding fields; per-run counts in the EXTRACTION-LOG 'cyclic-tail-residue' event.
- **legacy-encoded loc files recovered-or-marked** [I-3] — 7 Data\Languages .txt file(s) are not valid UTF-8 (incident I-3, investigated in docs/research/s5-legacy-encoding.mdx): 75 legacy segment(s) round-trip-decoded losslessly under the declared codec(s) cp1250; 5 unjustifiable byte run(s) — the fleet-corrupted coordinate strays — emitted as declared U+FFFD, the glyph healthy locales already ship verbatim at that line. Per-segment offset/hex/recovered-or-FFFD rows: localization/_ledger/encoding-residue.jsonl.
- Audio/video offload — [DR-2026-08-18-media-scope]: catalogued in place; proposed reverse-move manifest emitted at directory granularity; no pack-held copies exist until the owner opts in.

## 4. Remaining theoretical surface + protocol placeholder

Seeded; filled by later pieces (spec §1 non-goals): entity-curation datasets over the typed dumps, the relink layer (pairwise join matrix, UI-link→schema map, `RELATIONS.md`, locale availability), logic-layer derivations from `decompiled/_structure/`, demo-diff pass (dropped until a demo install exists — questions.md Q2).

### Protocol layer — PLACEHOLDER (explicitly seeded)

Single-player title: owes either the proof of no surface or an
inventory of Steam achievements/cloud saves/telemetry endpoints.
Seeded empty here; a later piece owns the content.

## 5. Dataset-era reconciliation (CLOSURE-1 phase-1 closure, 2026-08-25)

The six accepted datasets (`extracted/data/{characters,achievements,endings,
dialogue,cartridges,documents,scenes}/`) are reconciled here against their
sources and against each other, per Principle two. Consolidated gap ledger:
[`data/missingdata.md`](data/missingdata.md) (83 entries: owner-call /
derivable-later / measured-absence). Canonical relink layer assembled this
pass under `extracted/relinks/` — see §5.3.

### 5.1 Entity coverage

| Dataset | Entities | Measured how |
|---|---|---|
| characters | **24** personages (14 mita + 10 player) + 26 stub-ladder candidates | `personages.jsonl` data-row count == S1 registry sizes 10@48/14@301 byte-for-byte (AC-1) |
| cartridges | **23** cartridges + **17** minigames (+2 candidates) | row counts == C1 literal split (23 keys, 13/10 by slot) and the four §3.2 registries |
| achievements | **26** rows | registry size == store 26 == per-locale `Achievements.jsonl` count ×34 (AC-A1 fail-fast) |
| endings | **4** endings (3 anchors + peaceful stub) · **371** choice nodes · **1555** branch edges · **5** flag tables | AC-B1/B2 pinned sweep over all 51 containers; rerun id-set stable |
| dialogue | **2,839** nodes · **3,776** edges · 19 level graphs | census == ASL == independent filename recount (AC D1); SPEC's "thousands [unverified]" resolved exactly |
| documents | **14** profiles · **166** world documents (160 notes + 5 paper parts + novella) · **8** books | AC-1/AC-2 censuses; note dedupe arithmetic in `_meta.dedupe`; books availability derived from disk |
| scenes | **24** scene rows · **57** links · **986** POIs · **24** spawn tables | S1 tuple-match ×20 story levels vs World dumps; position-truth labels on 100% of POI rows |

### 5.2 Join coverage and locale coverage

Canonical relink tree `extracted/relinks/` (assembled CLOSURE-1 from the
parked dataset files; provenance + adjudications in
`relinks/_assembly-provenance.jsonl`): **25 relation files, 1,159 join
edges**. Placement/identity ownership rulings applied: cartridges owns pickup
placement (DS-4 §1), characters owns identity joins — the three-way
character↔cartridge emission is consolidated into ONE authoritative file;
the DS-6 placement restatement is excluded from the canonical tree and
recorded. Dialogue contributes its two relink-family artifacts inline
(residue join, speaker-theme mapping). Three meta-only members ship their
measured absences as data (`cartridge--scene-placement`, 
`minigame--choice-condition`, `ending--branch-edge` = 0 feeds edges).

| Pair family | Edges | Mechanism split |
|---|---:|---|
| character↔achievement / cartridge / dialogue-speaker / outfit / scene-membership | 110 | hard + logic/inferred per row (`status`/`missing_fields` carried) |
| minigame↔achievement / choice-condition / outfit-unlock / scene-carrier | 100 | 10+10 attributed award binds (3 hard + 1 logic), 76 carrier co-presence hard, J6 absence |
| document↔achievement / character / event-wiring / minigame / scene-membership | 792 | serialized persistent calls + census joins, hard |
| achievement↔award-site / ending · cloth-site↔outfit | 16 | hard reverse indexes |
| scene↔chapter / dialogue-pool / objective-hints / save-vocabulary | 126 | hard client pointers |
| dialogue-node↔encoding-residue · speaker-theme↔character | 15 | residue join hard; theme mapping inferred/curation |

Locale coverage (pivot EN is range authority everywhere; cells derive from
disk presence, never asserted):

| Surface | Coverage | Evidence |
|---|---|---|
| characters pointers (name+bio) | 24×34 = **100%**, zero U+FFFD | AC-2 |
| achievements display names | 26×34 = **100%** | AC-A1/A2 |
| dialogue text pool | pivot ranges 100%; cells: 646 present / 33 filler / 1 contentless of 680; 4 locale tail deltas ledgered | AC D2/D3, `_ledger/locale-parity.jsonl` |
| cartridges categories | 4 categories ×34 present = **100%**; Arabic MakeManeken −1 tail renders filler | AC-4/AC-9 |
| profile lore/name pointers | 14×34 = **100%** | DS-5 AC-3 |
| book page art | 264/272 cells = **97.1%** (Location House 136/136; Location19 128/136 — zh-Hans/Hant lack 4 pages each) | books.jsonl derived from disk |
| scenes chapters/hints | 15 non-zero chapter pointers resolve ×34; hint pools resolve where the category exists; `LocationHint Location18` contentless ≠ missing | AC S2/S10 |

`extracted/relinks/locale_availability.jsonl` now exists (arbiter residue (c)
closed): **2,686 rows** = 680 dialogue bucket cells (seeded verbatim from
`dialogue/availability.csv`) + 1,734 category-presence cells measured from
disk (achievements/cartridges/characters categories, scenes Menu + all 20
quest pools + all 21 LocationHint stems) + 272 book-page cells copied from
`books.jsonl`. Reruns are byte-identical (tree sha256 stable across two
assembly passes).

### 5.3 Acceptance-criteria scoreboards (every dataset)

| Dataset | Scoreboard | Verifier surface |
|---|---|---|
| characters (B-1) | **10/10 PASS** (AC-1…AC-10) | scripted repo-side checks; build-log B-1 |
| achievements (B-2 Part A) | **7 PASS + 1 PENDING** (A5 icon export ledgered; official URLs interim) | emit-ledger + lint 413/413 cites |
| endings (B-2 Part B) | **8/8 PASS** (B1–B8) | contract scoreboard; 21/21 emit checks green |
| dialogue (B-3) | **8 PASS · 1 PARTIAL · 0 FAIL** (D6 structural ceiling 96.23%) | `_ledger/ac-scoreboard.json` independent checker |
| cartridges (B-4) | **10/10 PASS** | `build/selfcheck_cartridges.py` |
| documents (B-5) | **10/10 PASS** incl. live consume-by-reference reconciliation vs DS-4 (11-pair multiset byte-equal) | `build/selfcheck_documents.py` |
| scenes (B-6) | **S1–S10 all PASS**, 37/37 mechanical checks | `build/check_scenes.py` |

Cross-dataset reconciliations hold at closure: DS-5 placements ==
DS-4 `pickup_ref` mita-side subset (byte-equal multiset); scenes FlashTaker
POI joins match the same census (20 key-matched + explicit curation rows for
`mta`/`mtad2`/`mtacore`); dialogue terminals 548 and next-edge 2,150+12
baselines exact.

### 5.4 Residue summary consolidated

Carried forward from §3, updated by the dataset era:

- **Resolved by the dataset era:** R-E1-1 levelN dump depth (level-scene
  components now curated exhaustively by DS-3/DS-5/DS-6); R-E1-2 get-bool
  ambiguity (quarantined as flags, never rendered); R-E1-3 locale skew
  (encoded as data in `locale_availability.jsonl`); I-3 encoding residue
  (joined onto node `level14:Dialogue_3DText#5559`, traceable per locale).
- **Still open (ledgered with unblocks in `data/missingdata.md`):** native
  IL2CPP bodies (XC-1, owner-costed — gates 15 achievement predicates, all
  minigame scoring, safe-window percentages, outfit reflection targets);
  SPEC gap #1 chapter map (XC-2); transform stage S9 + global pathID index
  (XC-3, 76 pointer-only positions + spawn-table refs); sprite-pathID index
  (XC-4 → note content unresolved ×160); marker projection rerun (XC-5);
  PIPE stage registration fences (XC-6); RELATIONS.md roll-up (XC-7);
  protocol inventory (XC-8); demo diff pass (XC-9, owner install).
- **Unchanged P1 items:** GI cache catalogue-only (R-E1-4); cyclic typetree
  tails confined to dev-console scaffolding (I-S4); media offload awaiting
  the owner's catalogue decision ([DR-2026-08-18-media-scope]).

Completeness posture: the relink bare minimum [DR-2026-08-17-relink] bar 1
is satisfied at dataset-pair granularity for every pair the six datasets
reach; bar 2 (UI-link→schema map) is represented by the Version-category gap
(CH-1, documented, not worked around) plus the wiring/event-wiring indexes;
bar 3 (competitor floor) rides `competitor-research.md`'s applied-delta
joins (J1–J13 cited throughout the specs). The pairwise roll-up catalog
(`RELATIONS.md`, XC-7) is the one doctrine artifact not yet written and is
ledgered as derivable-later, not claimed.
