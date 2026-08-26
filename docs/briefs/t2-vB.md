# Brief t2-vB — Verifier B on T2 UI style scout (spec-completeness lens)

Fresh verifier subagent of the MiSide orchestrator. CANNOT spawn agents;
never run `git`; read-only outside your deliverable. You VERIFY, you edit
nothing. Do NOT Read full-resolution images (3 agents died that way);
thumbs under `design/refs/screenshots/thumbs/` are safe if needed.

## Check

`C:\_reps\game-databases\MiSide\docs\research\ui-style-scout.mdx` against
its mission spec `docs/briefs/T2-ui-style-scout.md`:

1. All six analysis areas delivered? (palettes / typography impressions /
   UI chrome patterns / glitch motifs / light-vs-dark recommendation /
   anti-genericism check)
2. Token recommendations: 6–10 CONCRETE rows (name, value, usage) — count
   them; vague "consider warm tones" rows don't count.
3. Every claim file-tied to a thumb/original filename? List any orphan
   claims.
4. Hexes marked `[sampled]` vs `[unverified]` honestly separated? Any
   `[sampled]` that looks like a stock palette value rather than an image
   sample (flag for t2-vA cross-check).
5. Usability for the next consumer: could a designer turn this table into
   `design/tokens.css` without guessing? Name what's missing if not.
6. Anti-genericism section actually names clichés to avoid (not generic
   advice)?

## Deliverable

`C:\_reps\game-databases\MiSide\docs\research\verifications\t2-vB.mdx` —
per-check results; final line exactly `VERDICT: PASS` or
`VERDICT: FAIL — <one line>`. ≤12 lines total.
