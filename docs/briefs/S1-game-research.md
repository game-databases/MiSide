# Brief S1 — game research + competitor inventory (MiSide)

You are a research subagent launched by the MiSide orchestrator. You CANNOT
spawn other agents — do all work yourself. Work ONLY inside
`C:\_reps\game-databases\MiSide\` and read-only everywhere else in the repo.
Never touch other games' directories. Never commit to git.

## Read before anything else

1. `C:\_reps\game-databases\AGENTS.md` — IN FULL (binding repo rules).
2. `C:\_reps\game-databases\_foundation\extraction-doctrine.md` — IN FULL,
   especially "Relink bare minimum" bar #3 (competitor relinking floor).
3. `C:\_reps\game-databases\_foundation\site-sections.md` — IN FULL (section
   families + tool-discovery process).
4. `C:\_reps\game-databases\_foundation\design-standard.md` §2 (reference sites).
5. `C:\_reps\game-databases\MiSide\README.md`.

## Established facts (do not re-derive)

Game: **MiSide** — Steam appid **2527500** (released 2024-12-10), free **Demo**
appid **2527520**, soundtrack DLC **3404450**. Developer AIHASTO, publishers
IndieArk + Shochiku. Unity engine. Single-player narrative horror/romance with
visual-novel elements. Store-listed languages (30): English*, Russian*,
Japanese*, Simplified Chinese*, French*, German*, Korean, Italian, Spanish-Spain*,
Ukrainian, Turkish*, Polish, Portuguese-Brazil*, Portuguese-Portugal*,
Spanish-Latin America*, Vietnamese, Hungarian, Indonesian, Thai, Swedish,
Romanian, Traditional Chinese, Persian, Serbian, Filipino, Croatian, Bulgarian,
Czech, Belarusian, Kazakh, Slovak (* = full audio).

## Deliverable 1 — `docs/research/game-research.mdx`

Verified public-knowledge research on MiSide's CONTENT UNIVERSE, written for an
extraction planner. Sections:

1. **Game structure** — how the game is organized (chapters/story progression,
   the apartment/metaspace loop, cartridge mini-games, endings). How many
   chapters/endings are documented.
2. **Characters** — every named Mita variant + human/NPC characters the
   community documents, with one-line descriptions and source links.
3. **Items & collectibles** — item categories the community tracks
   (cartridges, keys, documents/notes, outfits/skins if any).
4. **Mini-games** — each embedded mini-game (rhythm, cooking etc.), its
   mechanics and score rules as far as publicly described.
5. **Achievements** — total count, notable ones, Steam achievement page URL.
6. **Endings & choice structure** — documented branching points.
7. **Patch/version history** — release timeline, major content updates, current
   version label.
8. **Candidate data model** (YOUR analysis, clearly marked as inference):
   candidate entity kinds (character/mita-variant, location/scene, item,
   cartridge/minigame, document/lore-page, achievement, ending, dialogue-node,
   outfit…) and candidate relation families (character↔scene, item↔location,
   document↔location, ending↔choice, minigame↔cartridge…). This seeds the spec.

Every factual claim carries its source URL inline. Mark uncertain claims
`[unverified]` rather than guessing. If web fetches fail or return blank,
retry once with an AI-crawler User-Agent (e.g. `-A "Mozilla/5.0"` fallback or
OAI-SearchBot/Claude-User style UA); if still blocked, record it as a finding
line and move on — one attempt per wall, never retry into challenges.

## Deliverable 2 — `competitor-research.md` (pack root)

The relink-floor artifact ([DR-2026-08-17-relink] bar #3). Analyze at least
**three independent community wikis/databases** for MiSide (candidates: the
Fandom wiki, any wikily.gg / wiki.gg presence, RU-language wikis, guide sites,
Steam community guides index). For EACH source:

- URL, language(s), coverage breadth (entity kinds modeled);
- the RELATIONSHIP MODEL it actually surfaces: which entity↔entity relations
  are rendered as links (character↔chapter, item↔location, quest↔reward…),
  which exist only as prose;
- structural weaknesses (dead ends, no cross-linking, JS-only content, no
  locales, ads-over-data).

Then an **APPLIED DELTA** section — mandatory: concretely which joins OUR
database will add because we hold the extracted corpus (e.g. "Fandom lists
documents as prose pages with no document↔location join; we emit
document↔scene from placement data"), mapped onto the candidate relation
families from Deliverable 1 §8. A source list without this applied delta does
NOT meet the bar.

## Rules

- No legal/license/EULA commentary anywhere (repo rule 2) — record provenance
  facts only.
- Documentation style: MDX-flavored Markdown, tight anchor-style cross-links
  between your own headings where useful.
- Do not fabricate counts or dates; cite or mark unverified.
- Your final message: a ≤15-line summary of findings + both file paths.
