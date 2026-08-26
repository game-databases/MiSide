# MiSide — Tools Plan (Phase 3 scoring)

Authored 2026-08-24 by the Documentator pass (brief T-P1-toolsplan). Fulfils
spec gap 3: the `tools:` block in [spec.md](spec.md) is a deliberate STUB that
demands ≥5 evidence-linked, scored ideas via the site-sections tool-discovery
process before the pack counts as tool-planned (launch gate D5; spec §Tools
overview, §Section map row 5, §Spec gaps item 3). Inputs, read in full this
pass: [spec.md](spec.md) · [competitor-research.md](competitor-research.md) ·
[game-research.mdx](docs/research/game-research.mdx) ·
[ui-style-scout.mdx](docs/research/ui-style-scout.mdx). This pass wrote only
this file.

Shorthands follow spec.md: **D1** = game-research.mdx · **COMP** =
competitor-research.md · **T2** = ui-style-scout.mdx · **E1** =
explorer-e1-hands-on.mdx · **PIPE** = pipeline-run_all.mdx.

---

## 1. Declared rubric

Five criteria, 1–5 each, equal weight, total 25. Ties break on higher Player
value, then higher Data feasibility. Scores below are checkable arithmetic —
no hidden weighting.

**P — Player value.** Anchored to expected active use during a playthrough
window. The rubric's nominal ceiling (8–16 h/day) presumes a live-service
companion kept open beside a persistent game; a finished single-player title
cannot honestly reach it (spec axes: platforms none-declared, lifecycle live
but content-finite). The practical ceiling here is **session-companion** —
open beside every play session and revisited across runs — which scores 5.
5 = session-companion · 4 = consulted at decisive moments every run · 3 =
recurring reference in specific segments · 2 = occasional lookups, bursty ·
1 = one-look novelty. Upside only if Peaceful Mode ships its day-night /
shopping loop (D1 §1), the sole credible daily-use path.

**D — Data feasibility vs extraction artifacts.** 5 = spine verified
end-to-end on disk today · 4 = primary on disk, enrichment is routine
decompile · 3 = mixed verified + P5/decompile-gated · 2 = core gated on the
P5 levelN probe (R-E1-1) · 1 = needs unevidenced artifacts.

**X — Differentiation vs competitors.** Judged strictly against COMP S1–S5
(EN Fandom, RU Fandom, ≥100 Steam guides, Wikipedia, official Steam surfaces).
5 = modeled nowhere and derived from joins competitors cannot hold (COMP net
advantages 1–5) · 4 = modeled nowhere, adjacent prose exists · 3 = strict
supersedure of manual tables · 2 = parity with common checklist practice ·
1 = behind competitors.

**C — Build cost (higher = cheaper).** 5 = one decompile/table pass, no new
components · 4 = standard entity modules over existing primitives · 3 = one
novel interactive component + moderate pipeline · 2 = heavy: authored
artwork, new scene parser, custom canvas/SVG · 1 = multi-month platform.

**S — Soul-fit (T2 motifs as semantics, not decoration).** 5 = the game
already frames this exact kind of surface in its own UI · 4 = strong motif
mapping · 3 = generic data surface wearing motifs · 2 = fights the dual
cozy/horror register · 1 = alien.

---

## 2. Ranked field (7 ideas — spec stub carried 6 lanes; the changelog
differentiator added as a 7th)

| Rank | Tool | Spec lane | P | D | X | C | S | Total | Stub (promptForDB) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Ending Condition Explorer | ending-condition-explorer | 4 | 3 | 5 | 3 | 5 | **20** | HIGH |
| 2 | Dev-Console Command Reference | dev-console-command-reference | 2 | 4 | 4 | 5 | 5 | **20** | MEDIUM |
| 3 | Owned Scene Map + Collectible Planner | owned-scene-map | 5 | 2 | 5 | 2 | 5 | **19** | MEDIUM |
| 4 | Collection Completion Trackers | collection-completion-trackers | 4 | 5 | 2 | 4 | 4 | **19** | HIGH |
| 5 | Minigame Rule Revealer | minigame-rule-revealer | 3 | 4 | 4 | 3 | 5 | **19** | HIGH |
| 6 | Dialogue Database Browser | dialogue-database-browser | 3 | 3 | 5 | 3 | 4 | **18** | HIGH (text) / MED (graph) |
| 7 | Build Diff Viewer | *(section-map row 15 differentiator)* | 2 | 3 | 5 | 3 | 5 | **18** | HIGH |

Reading: rank 1 wins on differentiation × soul-fit × moderate cost; rank 2 is
the efficiency pick (cheapest possible ship, capped by tiny audience); rank 3
has the highest raw player value in the pack and the worst data gate.

---

## 3. The tools

### 3.1 Ending Condition Explorer — 20/25 (rank 1)

**What it does.** Interactive graph over the three endings (D1 §6) and their
full condition sets: the six "Conditions Met" prerequisites including the two
*negative* conditions ("avoid looking in the vent" ch 2, "refrain from looking
in the oven" ch 0), the wardrobe/stay branch at the ch-3 demo boundary, and
the safe's numeric upload-progress windows (17% ch 4 / 98% ch 18 / empty
ch 19). The visitor walks a chapter timeline, toggles choices, and the tool
shows which endings remain reachable and when missable windows are open —
exactly what COMP J1 says nobody models (S1 keeps it as six prose bullets
with unmodeled negative conditions; spec relations block names this the
flagship derived join).

**Feeds (extraction artifacts).** `CODE` — Il2CppDumper `dump.cs`
(288,102 lines / 6,281 types, E1 step 2) → decompiled condition checks +
MenuEnding under `extracted/decompiled/` (doctrine per toolchain T1 §3);
`LEVELS` flags post-P5 (spec entities choice_node, readiness unverified);
emits typed `ending ↔ choice_node` edges into `extracted/relinks/`.
Public reconciliation skeleton: D1 §6.

**Interaction sketch (T2).** Choices render as the game's own mid-screen
choice pills — vivid magenta-purple, keycap-bracket chips (T2 §3
choices/captions, "TAKE PILLS" precedent). Negative conditions wear the VHS
corruption hover — banding + RGB split marks the compromised path as state,
not decoration (T2 §4.1, §7.5). Flag ids and window percentages print in CRT
green machine voice (T2 §4.4); the reachable-ending verdict lands as a
gradient pill (T2 §6 accent-gradient recipe).

**MVP cut.** Static read-only graph of the documented set (6 prerequisites +
2 negatives + 3 windows, D1 §6), hand-checked against the decompile;
toggle-interactivity arrives once extracted flag polarity confirms it.

**Risks.** Thin flag universe — only 6 of "presumably many" choices are
publicly documented (D1 §8 gaps), so the graph may stay small even after a
clean decompile. Wrong polarity = actively harmful advice in a game with a
Missable achievement tag (D1 §5); mitigation: every edge prints its source
stamp in machine voice (user-facing provenance per AGENTS rule 3 class).
Decompile under-delivery leaves a pretty stub.

**Score rationale.** P4 — consulted at every ending-relevant moment (ch 0–3
setup, ch 4/18 windows) and on replay hunts · D3 — checks sit in pending
decompile + P5 flags; public skeleton documented · X5 — COMP J1: negative
conditions modeled nowhere · C3 — one novel graph component; pipeline is
ordinary relink emission · S5 — the game itself renders this surface as
choice pills (T2 §3).

**Stub (promptForDB).** HIGH — D1 §6 fully seeds structure, labels, and
windows today; decompile swaps real flag ids in place, no schema change.

### 3.2 Dev-Console Command Reference — 20/25 (rank 2)

**What it does.** Registry of the in-game debug console — OpenSettings /
OpenFunctions / OpenAddons / OpenResources / OpenEditor / OpenLevels /
ToggleDebugUnity / OpenData + ConsoleCheats discovered in E1 step 7, plus
`setfps` / `skipdialogue` / `triggershow` from the 0.93 notes (D1 §7) — each
mapped to the entities it touches (`triggershow` → trigger volumes, COMP
J14). Today this exists only as one patch-notes table (COMP J14).

**Feeds.** `CODE` ConsoleInterface (class #1441, E1 step 7) decompile +
`LIT` stringliteral.json (619,523 B, E1 step 2) scan for command strings;
corroboration against 0.93 patch notes (D1 §7). Emits `debug_command ↔
affected-entity` edges (spec relations, COMP J14 row).

**Interaction sketch (T2).** The one surface where the CRT terminal register
is *native*: green pixel/mono text `#08cb05` on near-black `#101010`, rows
printed as terminal output (T2 §4.4 machine truth; steam-ss8 wall screens,
LCD minigame precedent). Copy-to-clipboard actions use keycap chips (T2 §7.7).

**MVP cut.** One reference table, ~10 commands (est-scale ~10 unverified,
spec entities debug_command): name, effect, affected-entity links, cheat-flag
marker. A day of decompile reading.

**Risks.** Hard audience ceiling — curiosity/glitch hunters and future
speedrunners, not the mainstream run (P2). Cheats adjacency demands strictly
factual effect descriptions; invented behavior violates the no-authored-data
rule (spec Non-goals). Count may stay ~10 forever.

**Score rationale.** P2 — occasional lookup surface · D4 — handler class and
literals already located (E1 step 7); routine decompile · X4 — patch-note
prose is the adjacent source; nobody structures it · C5 — cheapest tool in
the field · S5 — CRT terminal is the game's own machine-voice surface (T2
§4.4).

**Stub (promptForDB).** MEDIUM — command names are known now (E1 step 7 + D1
§7); effects must ship marked `[unverified]` until the decompile lands — a
stub may hold placeholders, never guessed behaviors.

### 3.3 Owned Scene Map + Collectible Planner — 19/25 (rank 3)

**What it does.** Authored schematics of the apartment hub plus per-location
and per-version-space layers (spec maps.layers) carrying client-derived
markers: cartridges (exact placement coordinates replacing contradicting
guide prose — COMP J2; the Ghostly Mita ch 9 vs ch 10 conflict is the
cautionary tale, COMP findings), profiles, secrets, save points, minigame
access, monsters, travel gates (spec maps.coordinate-sources). Two-way links
with entity pages; URL focus state per spec §Section map row 2. No
Map-Genie-class incumbent exists in the niche (COMP negative findings;
corroborated and scoped by the §7 tool-site sweep — Map Genie's complete
2,296-game sitemap carries zero MiSide entries, while gaming.tools itself
proved unfetchable this pass) — the map alone would be the largest
structured-data surface in the MiSide ecosystem.

**Feeds.** `LEVELS` level0–23 scene transforms + pickup triggers (unparsed —
R-E1-1, PIPE next probe P5; spec maps.readiness ACHIEVABLE, blocker = the
parser); `LOC` LocationHint* / Location* categories for room naming (E1 step
5); `ART` sprites for markers; authored imagery on top (spec maps.imagery-path).

**Interaction sketch (T2).** The dark-plum field is literally the space
behind the apartment (T2 §1.2, §7.1). Layer picker as cartridge-card grid —
header pill + square cells with per-cell counts, straight from the game's
inventory screen (T2 §3 menu/list, §7.4). Not-yet-mapped rooms render as
checkerboard void — designed emptiness, honest about gaps (T2 §4.5) and the
same visible-locked honesty discipline as COMP J11. Markers as rounded-square
cells (radius-md family, T2 §6).

**MVP cut.** Apartment hub + one location scene, cartridge + profile +
save-point markers, static SVG; pan/zoom and the focus-state URL contract
follow once P5 proves the rect-per-map transform assumption (spec
maps.coordinate-transform).

**Risks.** Hardest gate in the plan: every coordinate-bearing marker waits
on P5 (D2). Authored-artwork cost is real and recurring (new scenes per
location_scene, est-scale 20–40, spec entities). Transform assumption
unproven. Scope creep across 23 scenes.

**Score rationale.** P5 — session-companion ceiling: collectible routes are
played with the map open; the top Steam guide genre is exactly this demand
(COMP S3) · D2 — P5-gated core · X5 — no incumbent of any class (COMP
negative findings + §7 sweep, scoped there) and coordinates are a join
competitors cannot hold · C2 —
heaviest build: authored art + parser + canvas interaction · S5 — purple
void + cartridge-cell grids are the game's own visual language (T2 §1.2,
§7.4).

**Stub (promptForDB).** MEDIUM — room skeletons stub from the `LOC` Location*
family + the S1 Locations table, but coordinate-bearing markers must stay
visible-locked rather than faked (J11 discipline; spec Non-goals forbid
invented content). A stub map with honest locked layers beats a fake one.

### 3.4 Collection Completion Trackers — 19/25 (rank 4)

**What it does.** Signed-in checklists (spec §Section map row 8, accounts per
DR-2026-08-19-ugc-accounts) for the tracked sets: 26 achievements with global-%
context, 13 character + 10 player cartridges, ~12 Mita Profiles, 4+ outfits
with reflection notes (D1 §3, §5). Per-chapter grouping, missable warnings
(the wiki's own Missable type tag, D1 §5), set-completion progress.

**Feeds.** `RES` DataAchievements — 26 rows, the pack's one fully verified
three-way join: steamAchievement ↔ icon PPtr pathID ↔ lineTranslate →
Achievements.txt line (E1 step 3, spot-verified ACHI_supermegapuperplayer ↔
line 26 "Pro Gamer"); `STEAM` keyless global-% stats (COMP J12, rarest "Pro
Gamer" 10.5%); `LOC` Achievements.txt ×34 locales; outfit set from the cloth
families on disk (E1 step 3, spec entities); cartridge/profile sets from
`RES` TamagotchiGame_Cartridge* / profile containers — set readiness
**unverified** per spec entities (classes known via dump.cs E1 step 7;
objects not yet census-seen), placements additionally P5-gated.

**Interaction sketch (T2).** The game's own HUD grammar is a tracker UI
already: pill gauges with white outline and pale-pink fill, circular icon
caps, currency-pill counters (T2 §3 HUD) — set progress renders as literal
pill gauges. Set groups as category panels: header pill + square cells with
counts (steam-ss2 menu, T2 §3). Missable rows flagged alarm-red `#fc0f43`
(danger accent, T2 §4.3).

**MVP cut.** Achievements tracker live on the verified join + Steam %;
cartridge/profile checklists grouped by chapter with guide-level
attributions explicitly labeled provisional until coordinates land (the
Ghostly Mita conflict shows why the label matters, COMP findings).

**Risks.** Concept parity — every Fandom and half the Steam guides are
checklists (COMP S1/S3), so X2 is honest; the moat is derived accuracy,
34-locale names, and per-build drift flags, not the concept. Account-system
prerequisite. Upside: Peaceful Mode's teased costume unlocks (D1 §1) extend
the outfit set.

**Score rationale.** P4 — consulted throughout any completion run; two
collection achievements sit at 11.9% / 13.8% global, so completions are rare
and help is wanted (D1 §5) · D5 — spine verified end-to-end today · X2 —
parity concept · C4 — checklist primitives + accounts · S4 — HUD/menu
grammar maps directly (T2 §3).

**Stub (promptForDB).** HIGH — the strongest stub in the field: achievements
fully verified now; sets stub from published counts (13 + 10 + ~12 + 4, D1
§3) and upgrade row-by-row at harvest.

### 3.5 Minigame Rule Revealer — 19/25 (rank 5)

**What it does.** Per-minigame pages exposing exact scoring functions — win
thresholds, coin counts, timers, per-song DDR scoring, Spacecar nitro/coin
economy (COMP J6) — replacing anecdotal guide prose ("beat 4 times out of
4"), plus interactive calculators for the grindy ones and per-build tuning
diffs (0.93 simplified the Spacecar boss and retuned coin visibility — D1 §4,
§7 — proof this data moves between builds).

**Feeds.** `RES` MinigamesController/Settings + CarSpace_* / MakeManeken_*
(on-disk, census-seen E1 step 3); `CODE` decompiled minigame managers for the
scoring functions (COMP J6); `LOC` MiniGame* (verified role, E1 step 5) for
×34 names; 0.93 notes seed the tuning-diff skeleton (D1 §7).

**Interaction sketch (T2).** The LCD handheld is the frame: blue plastic
shell, olive screen, chunky pixel font in `#08cb05` on near-black — the game
physically presents its minigames as data surfaces (T2 §3 LCD console), so
SCORE/threshold readouts speak pixel machine-voice natively. Control hints as
keycap chip + gradient label pill pairs (T2 §3). Old tuning values shown
under the corruption hover when diffs land.

**MVP cut.** Rule tables for all ~17 minigames (access medium + chapter +
publicly documented threshold, D1 §4 table) + working calculators only for
the first cleanly decompiled managers — Snake (25 apples), Penguin Piles
(best of rounds), Dairy Scandal (4 of 4).

**Risks.** Decompile depth will be uneven per manager. Analog/story minigames
(card game, Monster-Slap, Tic-tac-toe — no achievement, D1 §4) cap calculator
coverage. Tuning diffs idle until a second build exists (see 3.7).

**Score rationale.** P3 — consulted in bursts at each minigame attempt;
return visits driven by grindy achievements (Fly Console 25 coins) · D4 —
controllers/settings on disk; formulas are routine decompile · X4 — guide
prose is adjacent; exact functions exist nowhere · C3 — table pages + a
calculator component · S5 — the LCD console framing is supplied by the game
itself (T2 §3).

**Stub (promptForDB).** HIGH — the full 17-row table seeds from D1 §4 today;
formulas fill in at decompile without schema change.

### 3.6 Dialogue Database Browser — 18/25 (rank 6)

**What it does.** Node-keyed, speaker-joined, chapter-scoped transcript
database across all locales — the applied delta COMP J8: S1 hosts EN + RU
hand-pasted subpages with the other five locale links redlinked; the client
holds 34 dirs (spec Locale strategy). Browse by chapter/speaker/Mita,
cross-locale comparison per node, per-Mita dialogue modules embedded on
character pages. Ships as **data**, not per-node pages — static JSON API +
scoped views, exactly the declared shape in spec §Page inventory (the
seo-standard §5 uniqueness floor forbids thin node pages regardless of what
P5 measures).

**Feeds.** `LEVELS` DialogueChanger graphs (P5-gated, R-E1-1) for node
edges; `LOC` LocationDialogue* ×34 + Personages/Names for speaker joins
(join authority proven end-to-end, E1 steps 3/7); scale set by P5
("thousands" unverified, spec entities dialogue_node).

**Interaction sketch (T2).** Reproduce the game's dialogue band: translucent
pink fill, name-tag pill overlapping top-left, SPACE advance pill top-right
(T2 §3 dialogue box). Speaker views re-key accent + glow to each Mita's
palette — colour-is-identity (T2 §7.3). Spoiler-collapsed lines render as
VHS-noise strips until expanded (corruption-as-state, T2 §7.5). Long reading
sessions get the warm-cream secondary surface T2 §5 explicitly reserves for
long reading pages. Locale navigation stays route-coded per spec Locale
strategy — prefixes in URLs, never a same-page toggle; a side-by-side
two-locale comparison inside a node view is data rendering, not chrome.

**MVP cut.** Chapter/speaker browsable transcript views over the `LOC` pull
alone (real multilingual text, no P5 needed) + the JSON API day one; node
graph edges and cross-locale diff views after P5 fixes the corpus.

**Risks.** Scale unknown — naïvely thousands × 34 is six-figure mass; the
declared data-shape mitigates but the view layer still needs pagination
discipline. Spoiler exposure is inherent (transcripts are the plot);
default-collapse late chapters. Graph quality depends entirely on P5.

**Score rationale.** P3 — lore readers and the RU community dive deep but
episodically; quote-lookup traffic · D3 — loc text on disk with proven join;
node graphs P5-gated · X5 — all-locale node-keyed transcripts exist nowhere
(COMP J8; five redlinks) · C3 — browser views over emitted JSONL · S4 —
dialogue band literal; long-form reading strains candy chrome until the
cream register kicks in (T2 §5).

**Stub (promptForDB).** HIGH for text-only views (loc pull yields genuine
34-locale content pre-P5); MEDIUM for graph views (need real node edges —
stub graphs would be invention).

### 3.7 Build Diff Viewer — 18/25 (rank 7) — *the no-competitor differentiator*

**What it does.** Per-build, per-record diffs over versioned datasets — the
spec's §Section map row 15 "[CORE differentiator]" made tangible: save-point
rename lineage (`Cap`→`Cappie`, `Open Dialogue`→`Be Candid`, 0.921 — COMP
J9, D1 §1), minigame tuning deltas (0.93, D1 §4), locale additions across
v0.91/v0.921/v0.924 (D1 §7), cartridge placement drift (open question, D1 §8),
each record stamped buildId (spec automation.staleness-model per-record),
landing under the `/news/patch/{id}` shape (D5 ambition move 3, spec row 15).
No competitor diffs anything — COMP S3's guides are explicitly dinged for
staleness with "no diff discipline".

**Feeds.** Automation watches (appmanifest buildId + Steam news RSS pinning
patch dates, spec automation.watches); `LEVELS` checkpoint configs per build
(COMP J9); `extracted/relinks/locale_availability.jsonl` regenerated every
rerun (spec locale-cells/source-per-locale); minigame settings deltas (3.5's
artifacts). Field-level truth needs a second harvested build — the demo
appid 2527520 install decision (spec gap 5, DAQ) becomes strategically
relevant as a diff boundary (demo ends exactly at the ch-3 wardrobe choice,
D1 §6).

**Interaction sketch (T2).** The corruption language finally means exactly
what it says: removed/renamed strings render VHS-degraded with chromatic
fringing, current values crisp (T2 §4.1); deletions in alarm red `#fc0f43`,
additions in CRT green (T2 §4.3/§4.4); buildId stamps in pixel font —
machine truth about machine state. This is corruption-as-state with no
metaphor stretch at all.

**MVP cut.** Patch-note-derived lineage pages immediately: the 0.921 rename
table + locale-addition timeline (D1 §7) are real, citable content today;
field-level diffs arm automatically the first time a rerun sees a new
buildId.

**Risks.** May idle for months — the last public release-notes post is v0.93L
2025-06-13 (D1 §7); the demo boundary covers only ch 0–3. Honest mitigation:
ship the note-derived MVP now (zero waste — it is row 15's News/patch shape
regardless) and let the pipeline harden it on trigger. Scored honestly: X5
cannot rescue P2.

**Score rationale.** P2 — consulted in bursts at patch moments only · D3 —
note-derived lineage available now; field diffs need build #2 · X5 — no
competitor versions anything · C3 — diff rendering + per-record stamps on
existing emit pipeline · S5 — VHS corruption is literally what a diff shows
(T2 §4.1).

**Stub (promptForDB).** HIGH — D1 §7's timeline + the 0.921 renames seed
real pages today; per-record diffs append as builds arrive.

---

## 4. No-competitor ideas (explicit call-out)

Three ideas clear the "modeled nowhere in COMP S1–S5" bar, not merely
"better than the wiki": the **Ending Condition Explorer** (negative
conditions + progress windows modeled nowhere — COMP J1), the **Dev-Console
Reference** (commands live in one patch-notes table — COMP J14), and the
**Build Diff Viewer** (nothing in the niche versions anything — COMP S3
weaknesses). All three derive from joins competitors structurally cannot
hold (COMP net advantages 1–5). Per the brief, the changelog differentiator
was scored without sentiment: its X5 stands, its P2 is why it ranks last
while remaining strategically cheap.

---

## 5. Recommended Phase 3 build order

Ordered by **stub-first shipability**, not rank — and not strictly by the D
axis either (explorer D3 ships before revealer D4; map D2 before dialogue
D3): the sort key is how much of a tool can ship truthfully *today* from
documented or on-disk sources under the promptForDB contract above, which
is not monotone in D. Rank measures value; order measures shippable truth.
No stub ever fabricates a data row (spec Non-goals; J11 visible-locked
discipline).

1. **Collection trackers** (rank 4) — only tool with a verified-today spine
   (E1 step 3 three-way join + keyless Steam %). Builds the shared component
   kit (pill gauge, header-pill panels, keycap chips — shadcn/ui heavily
   upgraded per the spec Design direction mandate) that every later tool
   reuses.
2. **Dev-console reference** (rank 2) — one decompile pass over
   ConsoleInterface + `LIT`; cheapest full ship in the field; natural
   companion to wave-1 decompile reading.
3. **Ending explorer** (rank 1) — graph UI on the documented 6+2-condition
   skeleton immediately; real flag ids light up as decompile + P5 land.
4. **Minigame revealer** (rank 5) — rule tables from on-disk controllers;
   calculators follow each clean manager decompile.
5. **Owned scene map** (rank 3) — begin the authored apartment-hub schematic
   + honest locked layers now; the full marker pass executes behind the P5
   gate (highest-value tool in the pack; biggest single dependency).
6. **Dialogue browser** (rank 6) — text-only chapter/speaker views + JSON API
   from the loc pull; node-graph views once P5 sizes the corpus.
7. **Diff viewer** (rank 7) — standing infrastructure from day one:
   note-derived lineage pages ship immediately and harden automatically at
   the next buildId change or the demo-install decision (spec gap 5).

Waves 3–7 overlap freely once step 1's component kit exists; the P5 probe
(spec gap 1) is the critical-path unlock for steps 5–6 and half of step 3.

---

## 6. Cross-tool dependencies and shared risks

- **P5 levelN probe** gates the scene map entirely, dialogue node graphs, and
  ending/cartridge flag geometry (R-E1-1; spec missing-data item 1; PIPE
  agrees) — the single scheduling fact of Phase 3.
- **Decompile depth** gates ending conditions, minigame formulas, console
  effects — all three degrade gracefully to their documented stubs.
- **Second-build scarcity** (silent since v0.93L, D1 §7) caps the diff viewer
  and tuning diffs; the demo appid is the only near-term second corpus
  (spec gap 5).
- **Accounts** gate tracker persistence (DR-2026-08-19-ugc-accounts via spec
  row 8) — build after the component kit, before tracker polish.
- **Spoilers**: dialogue browser and late-game ending flags need a
  default-collapsed policy decided once, applied everywhere.
- **Peaceful Mode upside** (announced, Kickstarter-backed, D1 §1): shipped
  locked-stub capture (COMP J11) already feeds the trackers, map, and diff
  viewer with zero rework — the plan's optionality is deliberately priced in.

---

## 7. Tool-discovery competitor sweep (site-sections §Tools step 1)

Run 2026-08-24 (fixer pass F-TP1) from this host via curl. Traffic
estimates: **none recorded — no basis existed this pass** (no SEO API here;
search engines partially bot-walled), so that cell stays honest-empty
rather than fabricated.

| Probe (all 2026-08-24) | Fetch result | Competitor tool pages found | What exists vs not |
|---|---|---|---|
| gaming.tools `/miside`, then `/` | **403 across three UAs** — plain Mozilla, then OAI-SearchBot and Claude-User retries; wall, one attempt each | none verifiable | **Unverifiable this pass** — owed a re-run at the next patch sweep |
| DuckDuckGo HTML SERP: "MiSide interactive map cartridge tracker" | 200, 10/10 results parsed | none — 9 prose guides/articles (Pro Game Guides, Gameranx, Dot Esports, Neoseeker, ShowGamer, Wotpack, Yekpeak, SandJack, one Steam Community guide) + Fandom's generic `Special:AllMaps` shell | no calculator/tracker/map/planner ranks |
| Bing SERP ×6 (`MiSide calculator/tracker/planner/map/mapgenie`, `"gaming.tools" miside`) | identical non-query result sets per query → soft-block; **discarded, cited nowhere** | n/a | n/a |
| mapgenie.io/sitemap.xml (complete public index) | 200 — 2,296 game URLs parsed | **zero** MiSide entries | **Map Genie carries no MiSide map** (hard negative; corroborated by `/miside` → 404) |
| mapgenie.io/miside · game8.co/games/MiSide | both 404 | none | no tool hub at either namespace |
| miside.fandom.com/wiki/Special:AllMaps | 403 bot wall | unverifiable directly; COMP S1 already reads Fandom as database-only | Fandom's interactive-map feature **unconfirmed** for MiSide |

Community surfaces (subreddit/Discord tool mentions — also step-1 inputs)
were not re-mined this pass; COMP S1–S5 community coverage stands in for
them.

**Scoping consequence for the X5 claims (§3.3; §4's trio).** "No
Map-Genie-class incumbent" is **kept**, now on three legs instead of COMP
alone: (1) Map Genie's complete sitemap has zero MiSide maps — hard
negative; (2) the one clean SERP pull returns only prose guides, no
tool-class page; (3) gaming.tools itself and Fandom AllMaps are bot-walled
— **unverified, not confirmed absent**. The claim's honest scope is
therefore "no incumbent found on any surface fetchable this pass", not
"anywhere" — §3.3's wording above is amended accordingly, and this sweep
re-runs on the next major patch (site-sections step 1 mandate).
