# Brief R-FVC3 — Code Reviewer: verify F-VC3's fix round (MiSide site/)

Fresh Code Reviewer subagent of the MiSide orchestrator. CANNOT spawn
agents; `git log/show/diff` allowed; never write repo state; never
taskkill by image name (port-scoped PID only). Write ONLY
`docs/research/verifications/fvc3-review.mdx`. Disk minimal.

## Verify claims by RE-EXECUTION

Builder log: `docs/logs/F-VC3.log`. Diff: commit 1f651af3 — review via
`git show 1f651af3`.

1. Re-run in site/: `npm test` (29/29), hex lint, chrome parity ×34,
   `npx tsc --noEmit`.
2. **Save-key replacement** [highest risk]: new chips consume which
   fields? Verify they trace to dataset/relink fields (collectible_set,
   pickup scene refs) — no invented semantics (rule 8); grep for any
   remaining `.save_key`/flash_save_key rendering as visible text.
3. **Cartridge modules**: spot-check 2 cartridges' modules against
   `extracted/data/cartridges/relinks/` edges — counts and links must
   equal corpus truth; no transitive joins beyond pinned files.
4. **Art decline honesty**: players ×9 / locations wells — confirm the
   corpus absence claim yourself (query the datasets/relinks for any
   art pointer the fixer missed); if you FIND one, that's a blocker.
5. **Lift fix**: read CartridgeCard change — CSS-only? does it fire on
   keyboard focus too (a11y), or pointer-only?
6. Regression hunt: anything in the diff outside the 5 items?

## Verdict

Final line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`.
≤12 lines body. Severity-tagged findings.
