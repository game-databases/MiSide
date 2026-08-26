# Brief tp1-vA — Verifier on F-TP1's tools-plan fixes (drift + fetch spot-check)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
`git diff` allowed (never write). You verify; you edit nothing.

## Check

`git diff HEAD -- MiSide/tools-plan.md` vs the fixer's claims in
`MiSide/docs/logs/F-TP1.log`:

1. Exactly the 4 prescribed areas changed; no collateral edits.
2. **Fetch evidence spot-check:** independently re-fetch ONE of its claims
   via curl (e.g. Map Genie sitemap URL count, or gaming.tools 403 with
   default UA then an AI-crawler UA per promptForDB Note#6). Does reality
   match the table? Report actual numbers.
3. The "anywhere"→re-scope wording actually removes the overclaim.
4. Traffic cells: confirm they are honestly empty rather than invented.

## Deliverable

`docs/research/verifications/tp1-vA.mdx`; final line exactly
`VERDICT: PASS` or `VERDICT: FAIL — <one line>`. ≤8 lines.
