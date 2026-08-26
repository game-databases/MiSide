# Brief F-VC3 — Site Fixer: VC-3's 5-item list (MiSide site/)

Fresh Site Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`; touch ONLY `site/`. PROCESS SAFETY: never
taskkill by image name; port-scoped PID only. NOTE: a sibling session
owns CDP port 9341 — use a DEDICATED Chrome profile for your evidence
shots. Disk OK.

## Read

`docs/research/visual-critic-3.mdx` — adjudication + the 5 fixes.
Grades to defend: Home 8 · Search 9 · RU 9 · Motion 8 — do NOT regress
what already passes; scope changes narrowly.

## Implement ALL

1. **Save-key chips off UI**: `EntityDetailRoute.tsx:130` renders
   `stats: [c.save_key]` and `:151` flash_save_key as visible text
   ("mtakd" on /mita/mita-kind). Replace with reader-meaning fields
   (collectible_set, version label, global % from achievements data)
   or drop the chip. Machine-plane identity must never render as copy.
2. **Cartridge density**: cartridges are our emptiest detail pages.
   Add a buildModules branch consuming the PINNED joins that already
   exist in `extracted/data/cartridges/relinks/` (contains-minigames;
   pickup_ref container→location): modules w/ counts + links, same
   pattern Mita pages use. No invented joins (rule 8).
3. **Per-card art on index grids**: players 10/10, minigames 17/17,
   locations 24/24 cards are artless (banners alone don't count).
   Extend `indexArtFor` coverage from corpus identity art (tamagotchi
   family et al.); keep total <200 MB; manifest == disk invariant.
4. **Dialogue index `<title>`**: still generic "MiSide Database" while
   every other index is section-named (`sectionPages.tsx` metadata).
5. **Card lift dead code**: `hover:-translate-y-0.5` at
   `kit/CartridgeCard.tsx:52` computes transform:none under real
   pointer (split fires, lift doesn't). Make lift actually fire or
   replace with an effect that does; prove with computed-style eval.

## Verify before finishing

Re-run: build exit 0, tests, hex lint, parity ×34, tsc, curl subset.
THEN own evidence shots: /mita/mita-kind shows zero save-key text;
one cartridge detail page with ≥2 real modules; three arted card
grids; dialogue `<title>`; lift transform ≠ none under hover.
Kill servers/browser port-scoped; dedicated profile only.

RESUME NOTE (attempt 3): TWO prior fixer runs died to API errors.
The tree now carries their combined work: ALL five items appear
implemented (297 insertions incl. sectionPages/art.ts/contracts.ts;
per-card art for all three grids emitted; emitter artifacts + fresh
production build at 01:25 already exist). Do NOT re-implement. Your
job is NARROW: (1) spot-audit each of the 5 items in source (minutes,
not a re-derivation); (2) run the FULL verification block — build
exit 0, tests, hex lint, parity ×34, tsc, curl subset; (3) capture
the 5 evidence shots from the Verify section; (4) report per-item
state. If any item is genuinely missing, implement just that gap.

Final message ≤10 lines: per-item done-state + suite counts.
