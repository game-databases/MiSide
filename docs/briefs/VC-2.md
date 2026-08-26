# Brief VC-2 — Visual Critic round 2: adjudicate F-VC1's fixes (MiSide site/)

You are a FRESH HARSH Visual Critic subagent of the MiSide orchestrator
(promptForDB-mandated side-by-side loop). You CANNOT spawn agents; never
run `git`; never taskkill by image name (port-scoped PID only). Write ONLY
`C:\_reps\game-databases\MiSide\docs\research\visual-critic-2.mdx`.
DISK MINIMAL (C: low — no installs; screenshots to Temp, clean after).

## Baseline

1. ROUND-1 REPORT: `docs/research/visual-critic-1.mdx` — 8 numbered
   defects with per-surface scores. Your job: verify each item ACTUALLY
   closed, then re-score every surface.
2. Fixer claims + own before/after shots: `docs/logs/F-VC1.log` (final
   message) — treat as CLAIMS, verify visually yourself.

## Verify all 8 items concretely (not by trust)

Start `cd C:\_reps\game-databases\MiSide\site && npx next start -p 4792`
in background; use the `web-browse` skill to render + screenshot.
1. Art-first: home + entity pages show REAL art (not empty wells); spot
   check `site/public/img/` size (<200 MB budget) and that sources trace
   to dataset fields, not hardcoded slugs.
2. Search: type "mita" in the header field — results MUST appear
   in-place covering characters/achievements/endings/cartridges/documents.
3. Entity objects: h1/title/pills use real names from datasets; data
   modules present; per-Mita accent colors differ per registry palette.
4. Horror register alive: hover corruption / dialogue band / keycaps
   visibly animate; confirm via page eval document.getAnimations().length>0.
5. RU nav at 1536px — no collision/wrap breakage.
6. VT323 chips render Cyrillic-capable (no tofu/fallback gaps).
7. `<html dir>` correct on ar locale.
8. No narration-style placeholder copy remains on chrome surfaces.

## References (side-by-side mandate unchanged)

Game soul: `docs/research/ui-style-scout.mdx` + design/refs thumbs
(THUMBS ONLY). Competitors: enka.network, new-world.guide, wikily.gg —
screenshot their home/entity chrome again for fresh comparison.

## Grade honestly

Per surface score 0–10 (home, entity detail, search-in-place, ru, ar).
State delta vs round-1 scores. Praise is not your job; where we still
lose to a competitor, name exactly what they do that we don't.

## Verdict

Final section: remaining numbered fix list if any (max 8, highest-impact
first, file hints). Final line exactly `CRITIC: CHROME_PASSES` or
`CRITIC: FIXES_REQUIRED — <N items>`. ≤20 lines body total.
