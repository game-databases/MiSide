# Brief R-DS5 — Reviewer: dataset-documents spec (+ cross-spec check vs cartridges)

Fresh Reviewer subagent of the MiSide orchestrator. CANNOT spawn agents;
`git` never; read-only except your verdict file. Corpus:
`C:\_reps\game-databases\MiSide\extracted\`.

## Read

1. SPEC: `MiSide/docs/specs/dataset-documents.mdx` (419 lines)
2. SIBLING: `MiSide/docs/specs/dataset-cartridges.mdx` (Flash family).
3. Corpus ground truth.

## Checks

1. **profile_document anchor:** recount the 13 rows (11 FlashTaker + 2
   script-granted) and their DS-1 keying; confirm mta*/plr* ↔
   ACHI_mitastory(13)/ACHI_cartridgeplayers(12) split arithmetic.
2. **world_document census:** sample the 160-note dedupe (from 258 dumps)
   — does the dependency-load dedupe rule actually produce 160? Verify 5
   BlackRoom paper parts (indexPuzle 0–4) + 8 book textures.
3. **Negative findings:** reproduce ≥2 (no notes/documents loc category —
   Translation.jsonl single row; ComicBook = Colorful post-effect).
4. **Top risk honesty:** note content carrier unresolved (zero-field
   component) — is the spec's plan for content honest about this, or does
   it smuggle an assumption?
5. **CROSS-SPEC:** family boundary vs dataset-cartridges.mdx consistent?
6. ACs: sample 5 incl. the negative-invention grep + determinism.

## Verdict

`docs/research/verifications/ds5-review.mdx`; findings w/ severity; final
line exactly `VERDICT: APPROVE` or `VERDICT: NEEDS_REVISION — <N>`. ≤12 lines.
