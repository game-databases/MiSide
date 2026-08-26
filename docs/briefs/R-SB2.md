# Brief R-SB2 — Code Reviewer round 2: verify F-SB1 fixes (MiSide site/)

Fresh Code Reviewer subagent of the MiSide orchestrator. CANNOT spawn
agents; `git diff` allowed; never write repo state. **PROCESS SAFETY:
never taskkill by image name — port-scoped only.** Disk minimal.

## Check

Claims: `docs/logs/F-SB1.log`. Prior verdict: `sb1-review.mdx`
(2 blockers + 5 minors). Diff: locate F-SB1's changes via
`git log --oneline -- MiSide/site/src | head -3` / working tree.

1. **Blocker 1:** entity canonicals now locale-prefixed on prefixed
   routes; pivot bare; hreflang cluster intact (spot-check 3 routes via
   curl on a port-scoped `next start`, or exported HTML).
2. **Blocker 2:** sweep ALL sitemap partitions yourself — zero
   relative `<loc>`; robots Sitemap absolute.
3. **Minors ×5:** each actually fixed (npm test form runs green;
   `/ru` canonical; JSON-LD Organization standalone + inLanguage×34;
   RTL select SSR; parity script guard removed).
4. **Regression hunt:** chrome parity ×34, hex lint, unit tests re-run;
   nothing else drifted (`git diff` scope).

## Verdict

`docs/research/verifications/sb1-review-r2.mdx`; final line exactly
`VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`. ≤10 lines.
