# Brief F-S1B — Spec Fixer: apply d-s1-review findings to site-scaffold.mdx

You are a fresh Fixer subagent of the MiSide orchestrator. CANNOT spawn
agents; never run `git`. Touch ONLY
`C:\_reps\game-databases\MiSide\docs\specs\site-scaffold.mdx`.

## Read

1. `MiSide/docs/research/verifications/d-s1-review.mdx` — 3 revision
   findings + 2 advisory lows. Apply all five.
2. The spec itself; `spec.md` page inventory (for finding 2);
   `extracted/data/scenes/` contract (for finding 1).

## Fixes

1. **MEDIUM gate map:** bind AC-S7/§7 projection to the scenes-contract's
   source×space axis — `source=="inline" AND world-assumed` only;
   `space:"unknown"` inline rows and `parent-local` explicitly excluded
   with their dispositions stated.
2. **MEDIUM routing:** add disposition rows for ALL NINE omitted entity
   kinds (monsters, chapters, save points, game versions, outfits,
   travel gates, secrets, console commands, game modes) — each either a
   route pattern (with data source) or an explicit no-page ruling with
   reason. No silent omissions.
3. **MEDIUM-LOW:** add AC-S14 (sitemap generation: pivot + locale
   prefixes off availability ledger; lastmod from build) + assign
   schema.org JSON-LD ownership (which piece emits which types).
4. **Advisories:** record the reason hand-rolled chrome i18n was chosen
   over §2.20 libraries (one sentence); fix "12 T2 §6 rows" → 14.

No other edits. Final message ≤5 lines: per-finding before→after.
