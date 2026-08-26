# Brief F-VC2 — Site Fixer: VC-2's 7-item list + R-FVC1 minors (MiSide site/)

Fresh Site Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`; touch ONLY `site/`. PROCESS SAFETY: never
taskkill by image name; port-scoped PID only. Disk OK (~40 GB).

## Read

1. `docs/research/visual-critic-2.mdx` — adjudication of the previous
   fix round + the 7 remaining fixes below.
2. `docs/research/verifications/fvc1-review.mdx` — code reviewer's
   banked minors you also close.

## Implement ALL (priority order)

1. **Kill raw ids off-Mita** ("mta", "Books0", "mtaghost" in
   h1/title/breadcrumb/search rows): build a display-name layer from
   SHIPPED data only (registry human labels, `books.jsonl` texture
   basenames, cartridge gallery button labels); where a kind has no
   client name, title-case the slug honestly — NEVER invent lore names
   (rule 8). Consume everywhere ids currently render as text.
2. **Resurrect hover corruption**: real-pointer hover must change
   computed styles — fix the group-hover self-trigger in
   `kit/CartridgeCard.tsx`; drive `CorruptionHover active` from a real
   compromised flag in data (endings index already has
   `data-corrupted`).
3. **Art the five bare section indexes** (cartridges/players/minigames/
   locations/endings) via existing `indexArtFor` + corpus identity art;
   stay <200 MB total.
4. **Search cap**: `lib/search/searchRows.ts:78` silently drops 32 of
   52 "mita" matches. Kind-balance the limit and/or "+N more" chip so
   no matching kind is invisible.
5. **Entity module density**: counts/stats inside modules (not bare
   link lists); entity-named dialogue `<title>` (currently generic).
6. **Motion polish**: animate the VHS 404 block; SPACE keycap into the
   DialogueBand footer (`global-not-found.tsx`, `kit/DialogueBand.tsx`);
   verify document.getAnimations() > 0 on 404 + dialogue routes.
7. **Home featured module**: one featured-content row (map thumbnail
   from scenes data, or news/devlog strip) below the category grid.

Also close R-FVC1 minors: dialogue index rows leaking raw `levelNN`
titles ×4 (same predicate locations use); collapse the
`dialogue:dialogue:<lvl>` double namespacing; keyframe derives glow
color from `--ms-glow-pink` instead of restating rgba literals.

## Verify before finishing

Re-run: build exit 0, tests, hex lint, parity ×34, tsc, curl subset.
THEN re-screenshot your own evidence (web-browse skill): real-pointer
hover style delta, "mita" result count ≥40 visible or +N chip, five
arted section indexes, entity h1/title with zero raw ids. Kill any
server you started by port-scoped PID.

RESUME NOTE: a prior fixer run died to an API error MID-WORK after
implementing most items (uncommitted tree: 18 files, incl. searchRows
kind-balance, CartridgeCard hover fix, DialogueBand keycap, dialogue
titles, emitter display-name layer). AUDIT the working tree FIRST
against this list, finish only the gaps, then run the FULL verification
block (the prior run never completed it).

Final message ≤10 lines: per-item done-state + suite counts.
