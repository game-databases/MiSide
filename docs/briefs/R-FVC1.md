# Brief R-FVC1 — Code Reviewer: verify F-VC1's fix round (MiSide site/)

Fresh Code Reviewer subagent of the MiSide orchestrator. CANNOT spawn
agents; `git log/show/diff` allowed; never write repo state; never
taskkill by image name (port-scoped PID only). Write ONLY
`docs/research/verifications/fvc1-review.mdx`. Disk minimal.

## Verify claims by RE-EXECUTION (builder log: docs/logs/F-VC1.log;

diff base: parent of HEAD, i.e. commit before 78dc33a1 → run
`git show 78dc33a1 --stat` and review that diff)

1. Re-run: `npm test`, hex lint, chrome parity ×34, `npx tsc --noEmit`
   (in site/). Report actual counts.
2. **Search-id namespacing** (highest risk): F-VC1 namespaced dialogue
   ids to fix 15 MiniSearch duplicate crashes. Confirm (a) emitter
   dup-guard actually rejects future dupes, (b) NO other consumer of
   search rows / dialogue ids broke (grep all readers), (c) "mita" hits
   on a port-scoped `next start` you launch yourself.
3. **Entity modules from relinks**: spot-check 2 entities' data-module
   wiring against `extracted/relinks/` edges (no invented joins);
   dialogue-pool left unjoined is CORRECT per rule 8 (speaker slugs
   provisional) — confirm no silent half-join instead.
4. **Art pipeline**: `scripts/select-art.py` deterministic? manifest
   provenance recorded? public/img actual size <200 MB? any source art
   path OUTSIDE declared export roots?
5. **Accent re-key**: per-Mita accents derive from dataset registry
   palettes, not hand-picked literals (hex-lint passes = hint only;
   check tokens.css tier discipline).
6. Regression hunt: anything in the 335-file diff outside the 8 items'
   scope? Books de-slug naming honest ("Book 1" = client texture name —
   verify against data, not the claim)?

## Verdict

Final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤12 lines body. Severity-tagged findings.
